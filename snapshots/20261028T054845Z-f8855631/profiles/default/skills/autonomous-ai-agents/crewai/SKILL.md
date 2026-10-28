---
name: crewai
description: "Use when designing, building, testing, or troubleshooting multi-agent systems with the CrewAI framework, including agents, tasks, crews, flows, tools, memory, knowledge, MCP integrations, and CLI-managed CrewAI projects."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [crewai, agents, multi-agent, orchestration, flows, crews, tools, mcp, python]
    related_skills: [building-agents-with-sdks, secure-agent-skills, ai-engineer, python-dev]
---

# CrewAI Multi-Agent Framework

## Overview

CrewAI is a Python framework for building collaborative multi-agent systems. Use it when the problem benefits from **specialized role-playing agents**, explicit task handoffs, reusable crews, or higher-level flows that orchestrate agent crews with deterministic Python control logic.

CrewAI has two major building blocks:

1. **Crews** — groups of agents working on tasks, usually through sequential or hierarchical collaboration.
2. **Flows** — event/state-oriented Python workflows that can call crews, branch, persist state, accept human feedback, and coordinate deterministic application logic around LLM work.

This skill is for practical CrewAI development: project setup, agent/task/crew design, flow orchestration, tool integration, verification, and production-safety checks.

Current source-of-truth docs:
- https://docs.crewai.com/
- https://docs.crewai.com/llms.txt
- https://docs.crewai.com/llms-full.txt
- Package: `crewai` on PyPI

## When to Use

Use this skill when:
- Building a CrewAI project from scratch.
- Adding or refactoring CrewAI agents, tasks, crews, or flows.
- Deciding whether a workflow should be modeled as a crew, a flow, or plain Python.
- Integrating CrewAI tools, custom tools, MCP servers, apps, memory, or knowledge sources.
- Debugging CrewAI CLI, install, runtime, tool-calling, or multi-agent collaboration behavior.
- Evaluating a CrewAI system for reliability, observability, safety, cost, or testability.

Pair with:
- `building-agents-with-sdks` when comparing CrewAI against direct SDK loops, OpenHands, or other agent runtimes.
- `secure-agent-skills` when adding tools, MCP servers, package installs, remote APIs, file access, or code execution.
- `python-dev` when implementing project code, tests, packaging, or CI for a Python CrewAI app.
- `ai-engineer` when CrewAI is part of a broader RAG, product AI, or production LLM architecture.

Do **not** use this skill for:
- One-off chatbot wrappers with a single assistant and no meaningful orchestration.
- Repo-autonomous coding agents where OpenHands, Claude Code, Codex, or a custom coding-agent loop is a better fit.
- Workflows that are deterministic enough to implement as plain Python without LLM agents.

## Prerequisite Checks

Before editing or creating a CrewAI project:

1. **Inspect the local project** if one exists:
   - `pyproject.toml`
   - `uv.lock`
   - `crew.jsonc`
   - `agents/*.jsonc`
   - `src/**`
   - `tests/**`
   - `.env.example` / documented env vars

2. **Check installed versions** rather than assuming:
   ```bash
   crewai --version
   uv pip show crewai
   ```

3. **Know the two CrewAI installs:**
   - Global CLI: commonly installed with `uv tool install crewai` and upgraded with `uv tool install crewai --upgrade`.
   - Project environment: installed/synced by `crewai install` / `uv sync`; upgraded by changing the project dependency, for example `uv add "crewai[tools]>=<version>"`.

4. **Confirm API keys without printing secrets:**
   - Check only `SET` / `UNSET` state.
   - Do not dump `.env` or process environments.
   - Common keys may include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, provider-specific keys, search/tool API keys, or CrewAI platform keys.

5. **Read current docs for changed APIs** before relying on examples. CrewAI evolves quickly.

## Installation and Project Setup

Prefer `uv` for local Python environment management on this host.

### Install or upgrade the global CLI

```bash
uv tool install crewai
crewai --version
```

Upgrade when needed:

```bash
uv tool install crewai --upgrade
crewai --version
```

### Create a new crew project

```bash
crewai create crew <project-name>
cd <project-name>
crewai install
crewai run
```

Newer CrewAI projects commonly use JSONC-first configuration:

```text
crew.jsonc
agents/<agent_name>.jsonc
src/<package_name>/...
```

Do not assume all projects use the same layout; inspect generated files before patching.

### Upgrade project dependency

`crewai install` syncs the lockfile; it does not automatically bump constraints. To upgrade the project package, update and re-lock:

```bash
uv add "crewai[tools]>=<target-version>"
crewai install
uv pip show crewai
```

Use an explicit target version or documented range for reproducibility. Avoid unreviewed global upgrades inside an existing project unless the user asked for it.

## Core Concepts

### Agent

An agent represents a specialized role. Keep each agent narrow and concrete.

Good agent design includes:
- `role`: concise job identity.
- `goal`: measurable objective.
- `backstory`: domain framing, not a giant hidden prompt.
- tools/apps/MCPs only when required.
- explicit iteration and delegation settings.

JSONC-style agent example:

```jsonc
{
  "role": "{topic} Senior Researcher",
  "goal": "Find reliable, current information about {topic}",
  "backstory": "You identify relevant sources, extract key facts, and separate evidence from speculation.",
  "llm": "openai/gpt-4o",
  "tools": ["SerperDevTool"],
  "settings": {
    "verbose": true,
    "allow_delegation": false,
    "max_iter": 12
  }
}
```

Python-style agent example:

```python
from crewai import Agent

researcher = Agent(
    role="Senior Researcher",
    goal="Find reliable, current information about the requested topic",
    backstory="Expert researcher focused on evidence quality and concise synthesis.",
    verbose=True,
    allow_delegation=False,
)
```

### Task

A task should define exactly what work is expected and what output shape proves it is done.

Good tasks have:
- specific `description`
- concrete `expected_output`
- one accountable `agent`
- explicit context dependencies when needed
- guardrails or output models for critical workflows

```python
from crewai import Task

research_task = Task(
    description="Research the latest developments in {topic}. Include only sources from the last 24 months unless older sources are canonical.",
    expected_output="A concise briefing with 5-8 bullet findings and source links for each claim.",
    agent=researcher,
)
```

### Crew

A crew combines agents and tasks. Use it for collaborative LLM work where different roles genuinely add value.

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff(inputs={"topic": "AI agents"})
```

Start with `Process.sequential` unless there is a strong reason to use more complex coordination. Add delegation only after the single-path crew works.

### Flow

Use flows for deterministic orchestration around agent work:
- branching
- loops
- persistence
- human feedback
- combining multiple crews
- typed state
- external application steps

```python
from crewai.flow.flow import Flow, start

class ReportFlow(Flow):
    @start()
    def create_report(self):
        return self.report_crew.kickoff(inputs={"topic": self.state.topic})

flow = ReportFlow()
result = flow.kickoff()
```

A reliable CrewAI app often uses **flows for control** and **crews for judgment-heavy LLM work**.

## Design Heuristics

### Use a crew when

- The work benefits from multiple specialized perspectives.
- The task output is naturally reviewed, rewritten, researched, or critiqued by different roles.
- The workflow can be expressed as agent tasks with explicit expected outputs.

### Use a flow when

- You need deterministic branching or state transitions.
- You need human approval or feedback checkpoints.
- You need to call multiple crews or mix LLM work with APIs/databases/files.
- You need resumability, plotting, or clearer production orchestration.

### Use plain Python when

- The step is deterministic.
- A normal function, API call, SQL query, or validation rule can do it better than an agent.
- You need reliable parsing, arithmetic, transformation, or security checks.

### Start small

Build the thinnest useful system first:
1. one crew
2. one or two agents
3. one or two tasks
4. one provider/model
5. one verification command
6. one golden input/output fixture

Only add memory, delegation, MCP servers, broad tools, or hierarchical coordination after the minimal crew is observable and testable.

## Tool and MCP Integration

CrewAI agents can use local tools, platform apps, and MCP servers. Treat every tool as a capability grant.

Example shape:

```python
from crewai import Agent
from crewai_tools import FileReadTool, SerperDevTool

agent = Agent(
    role="Researcher",
    goal="Find and compile market data",
    backstory="Expert market analyst",
    tools=[SerperDevTool(), FileReadTool()],
    # mcps=["https://mcp.example.com/sse"],
    # apps=["gmail", "google_sheets"],
)
```

Security rules:
- Add only the tools needed for the task.
- Prefer read-only tools before write-capable tools.
- Do not give file, shell, browser, email, calendar, repo, or cloud tools to agents by default.
- For MCP servers, verify server origin, authentication, exposed tools, and data boundaries.
- For code execution or shell tools, prefer isolated sandboxes and explicit timeouts.
- Never let an agent decide to exfiltrate local files, credentials, emails, or private repo data.

## Memory and Knowledge

CrewAI distinguishes action capabilities from context capabilities:
- **Tools / MCPs / apps** let agents do things.
- **Skills / knowledge sources / memory** shape prompts and context.

Use knowledge sources for retrieved facts that should inform agent output. Use memory only when the application truly needs cross-run continuity and has a data-retention policy. Do not use memory as a dumping ground for transient task logs or secrets.

Checklist before enabling memory/knowledge:
- Data source is approved for the model/provider.
- PII and confidential data handling is defined.
- Retention and deletion behavior are understood.
- Tests cover stale or irrelevant retrieval.
- Prompt-injection risks from retrieved content are considered.

## Testing and Evaluation

Do not accept a model-generated answer as proof that the system works. Verify CrewAI apps with repeatable checks.

Minimum checks:

```bash
crewai install
crewai run
pytest
```

If the repo does not have tests, add at least one deterministic smoke test around:
- config loading
- crew construction
- flow construction
- tool wiring with fake/stubbed tools
- output parsing/validation

Use golden fixtures for representative inputs. For model-dependent outputs, test structure and invariants rather than exact prose.

Good assertions:
- required sections exist
- JSON output validates against schema
- citations are present when required
- unsafe actions are rejected
- tool calls stay within allowed paths/domains
- flow state transitions are correct

Avoid brittle assertions on exact LLM wording unless the output is fully mocked.

## Observability and Debugging

When debugging CrewAI behavior:

1. Reproduce with the smallest input.
2. Confirm CLI and project package versions.
3. Run with verbose logging if available.
4. Inspect which agent/task failed.
5. Check whether failure is model/provider, tool, prompt, config, or environment.
6. Replace real tools with stubs to isolate orchestration from external services.
7. Add a regression test or fixture once fixed.

Useful commands:

```bash
crewai --version
uv pip show crewai
crewai install
crewai run
pytest -q
```

If a CrewAI project uses plots for flows, generate or inspect the plot after structural changes to verify the workflow shape still matches the intended design.

## Production Readiness

Before shipping a CrewAI system, verify:

- **Model/provider control:** explicit provider/model selection, rate limits, fallbacks, and cost bounds.
- **Tool boundaries:** least-privilege tools, path/domain allowlists, timeouts, retries, and audit logs.
- **Secrets:** env vars or secret manager references documented; no secrets in prompts, logs, code, or fixtures.
- **State:** flow state is typed, persisted intentionally, and migration/cleanup behavior is documented.
- **Evaluation:** golden cases, adversarial cases, and regression tests exist.
- **Human checkpoints:** risky actions require approval before side effects.
- **Observability:** model calls, tool calls, retries, errors, and final outputs are traceable.
- **Failure modes:** provider outage, tool error, malformed output, missing env var, and partial completion are handled.

## Common Pitfalls

1. **Using agents for deterministic work.** If Python can compute or validate it reliably, do not spend tokens or add nondeterminism.

2. **Creating too many agents too early.** Multi-agent complexity hides failures. Start with one or two agents and add roles only when they improve measured output.

3. **Vague roles and expected outputs.** Agents need specific goals; tasks need concrete output contracts.

4. **Turning on delegation by default.** Delegation can cause loops, cost spikes, and unclear accountability. Enable it only when collaboration is needed and bounded.

5. **Giving agents broad tools.** File, shell, browser, email, and cloud tools expand blast radius. Add least-privilege tools only after a safety review.

6. **Confusing CLI version with project package version.** The global `crewai` CLI and project `.venv` package can differ. Check both.

7. **Expecting `crewai install` to upgrade dependencies.** It syncs the lockfile; use `uv add` or edit constraints and re-lock to upgrade.

8. **Ignoring model-dependent tests.** Exact prose will vary. Test schema, invariants, state transitions, and safety boundaries.

9. **Putting secrets in examples or logs.** Check only presence state and document env var names without values.

10. **Skipping current docs.** CrewAI APIs and project structure evolve; re-check docs before major changes.

## Verification Checklist

- [ ] Current CrewAI docs were consulted for any API or CLI behavior that may have changed.
- [ ] CLI version and project package version were checked when debugging installs or runtime failures.
- [ ] The workflow is intentionally split between crews, flows, and plain Python.
- [ ] Each agent has a narrow role, goal, and tool set.
- [ ] Each task has a concrete expected output and accountable agent.
- [ ] Delegation, memory, knowledge, and tools are enabled only when justified.
- [ ] Tool/MCP permissions are least-privilege and reviewed with `secure-agent-skills` for side effects.
- [ ] Secrets are referenced by name only and never printed.
- [ ] `crewai install` and `crewai run` or the project’s equivalent smoke command has been executed.
- [ ] Tests or smoke checks verify output structure, flow state, and safety boundaries.
- [ ] Production workflows have logging/tracing for agent steps, tool calls, retries, and failures.

## One-Shot Recipes

### Recipe: Create a minimal CrewAI project

```bash
uv tool install crewai
crewai create crew my-crew
cd my-crew
crewai install
crewai run
```

Then inspect generated files before editing:

```bash
python - <<'PY'
from pathlib import Path
for p in [Path('crew.jsonc'), *Path('agents').glob('*.jsonc')]:
    print('\n---', p)
    print(p.read_text()[:1200])
PY
```

### Recipe: Add a new agent/task safely

1. Read `crew.jsonc` and existing `agents/*.jsonc`.
2. Add one narrow agent with no tools first.
3. Add one task with a concrete expected output.
4. Wire the task to the agent.
5. Run `crewai run` with a known input.
6. Add tools only if the no-tool version proves insufficient.
7. Add or update a smoke test for the new output contract.

### Recipe: Decide crew vs flow

- If the problem is mostly “multiple expert agents produce/review a result,” use a crew.
- If the problem is “run a workflow with branches, state, external APIs, approvals, and maybe some agents,” use a flow that calls crews.
- If the step is deterministic, use plain Python and call it from the flow.

### Recipe: Debug a failing CrewAI run

```bash
crewai --version
uv pip show crewai
crewai install
crewai run
```

Then isolate:
1. Does config load?
2. Does crew/flow instantiate?
3. Does the provider call work with a minimal prompt?
4. Does each tool work outside CrewAI?
5. Does a no-tool version of the crew run?
6. Which task/agent first diverges from expected behavior?

### Recipe: Add an MCP server to a CrewAI agent

1. Confirm the MCP server owner, transport, auth, and exposed tool list.
2. Verify no tool exposes unnecessary file, shell, credential, email, repo, or cloud authority.
3. Add the MCP server only to the agent that needs it.
4. Run a single smoke input that requires exactly one intended tool call.
5. Inspect logs/traces to confirm no unexpected tool calls occurred.
6. Add an allowlist or wrapper if available.
