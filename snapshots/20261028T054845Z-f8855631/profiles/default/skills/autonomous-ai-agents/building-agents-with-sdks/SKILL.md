---
name: building-agents-with-sdks
description: "Use when designing, comparing, or implementing coding agents with SDKs, agent runtimes, or provider-compatible model layers. Helps choose the right stack, define the coding-agent loop, and avoid common integration mistakes."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [coding-agents, agents, sdk, agent-architecture, anthropic, openai, openhands, openrouter, orchestration]
    related_skills: [claude-code, codex, hermes-agent]
---

# Building Coding Agents with SDKs

## Overview

This skill is for building **real coding agents**: systems that inspect repositories, read and edit files, run commands, execute tests, verify outcomes, and iterate toward a working patch.

It is not about generic chatbot wrappers.
It is about choosing the right stack for software-engineering automation and designing the loop so the agent can operate safely and effectively inside a codebase.

The skill is intentionally split into:

1. **This top-level guide** — coding-agent architecture, stack selection, and implementation workflow.
2. **Deeper reference files** — provider/runtime specifics and reusable architecture patterns.
3. **Starter templates** — Python, TypeScript, and Node.js starting points.

Three distinctions matter constantly when building coding agents:

- **SDK** = a programmable library/API surface you embed in your app.
- **Agent runtime/platform** = a higher-level system that already runs most of the agent loop.
- **Model gateway/router** = a compatibility or routing layer for model access, not the coding-agent architecture itself.

Many bad coding-agent designs fail because they confuse these layers.

## When to Use

Use this skill when:
- You are building a coding agent that reads repos, edits files, runs tests, and validates changes.
- You need to decide between Claude SDKs, OpenAI SDKs, OpenHands, or OpenRouter.
- You need a clean architecture for repo access, tool contracts, execution policy, retries, and verification.
- You want to choose between a low-level SDK build and a higher-level coding-agent runtime.
- You want concrete implementation direction for Python, TypeScript, or Node.js coding agents.

Do **not** use this skill for:
- pure chatbots with no repo or tool loop
- generic workflow agents that do not touch code or shell execution
- UI-only comparisons disconnected from actual coding-agent behavior

## Fast Decision Matrix

### Start here

#### Choose **Claude / Anthropic SDKs** when:
- You want a careful custom coding-agent core with explicit tool-use loops.
- You want strong reasoning for debugging, patch planning, and stepwise repo work.
- You want direct provider control instead of a compatibility layer.

See: `references/claude-sdk.md`

#### Choose **OpenAI SDKs** when:
- You want a broad official surface for building coding agents.
- You want to start low-level and optionally move up to an agent SDK.
- You want strong support for tools, structured outputs, and agent orchestration patterns.

See: `references/openai-sdk.md`

#### Choose **OpenHands** when:
- You want a **ready-made autonomous coding-agent runtime**.
- Your main goal is repo-aware software-engineering automation.
- You prefer configuring and operating a coding-agent platform instead of building the loop from scratch.

See: `references/openhands.md`

#### Choose **OpenRouter** when:
- You already have a coding-agent loop or framework and want model portability.
- You need fast access to many models behind one API.
- You want routing/fallback flexibility more than provider-specific depth.

See: `references/openrouter.md`

## The Coding-Agent Core Loop

A real coding agent usually needs these layers:

1. **Task interpreter / planner**
   - Understands the coding task.
   - Decides whether to inspect code, run a command, edit files, or test.

2. **Repo inspection tools**
   - Read files
   - search code
   - inspect diffs
   - list relevant paths

3. **Execution tools**
   - run tests
   - run linters
   - run builds
   - run targeted scripts

4. **Edit tools**
   - patch existing files
   - create new files
   - make narrow, reviewable changes

5. **Verification layer**
   - confirm tests passed
   - confirm build succeeded
   - confirm expected files changed
   - confirm no unintended regressions appeared

6. **Policy / guardrails**
   - restrict destructive shell commands
   - control network access
   - require approval for dangerous actions

7. **State / summarization**
   - retain what files were inspected
   - record what hypothesis is being tested
   - compress prior context when the task grows

8. **Observability**
   - log prompts, tool calls, errors, outputs, and retries

If any of these are missing, the agent becomes brittle fast.

For a reusable deeper breakdown, see:
- `references/coding-agent-architecture.md`

## The Minimum Useful Toolset for Coding Agents

Start with a narrow, high-signal set of tools:
- `search_code(query, glob?)`
- `read_file(path)`
- `patch_file(path, diff)`
- `write_file(path, content)`
- `run_tests(scope)`
- `run_lint(scope)`
- `run_build(scope)`
- `git_diff(base?)`
- `git_status()`

Good coding agents often do better with **8 good tools** than with **30 vague tools**.

## Implementation Sequence

### 1. Define the coding-agent job clearly
Choose the job type first:
- **bug fixer**
- **test writer**
- **refactoring agent**
- **PR reviewer**
- **repo onboarding / code explainer**
- **CI failure investigator**

Different jobs need different tool emphasis and different verification logic.

### 2. Pick the control-plane level

#### Level A — direct model API + your own coding loop
Use when you want full control.

You own:
- planning loop
- repo search and file reads
- shell execution
- edit application
- verification
- retries
- summaries
- permission boundaries

Best for:
- productized coding agents
- internal engineering tools
- systems where correctness and observability matter more than speed of initial setup

#### Level B — provider agent SDK
Use when you want less boilerplate but still want application-level control.

You still own:
- product behavior
- repo integration strategy
- execution and verification policy
- production operations

Best for:
- fast internal tooling
- greenfield coding-agent products
- teams who want higher-level abstractions without giving up all control

#### Level C — coding-agent runtime/platform
Use when you want an opinionated agent that already behaves like a repo worker.

You mainly own:
- configuration
- credentials
- permissions
- environment setup
- evaluation and review

Best for:
- autonomous repo agents
- quick prototyping
- teams testing whether coding automation is worth deeper investment

## Design Tools Like Stable Engineering Interfaces

Each coding tool should have:
- a narrow purpose
- explicit typed inputs
- a bounded output shape
- deterministic failure modes
- timeout behavior
- retry policy
- verification path

### Good tool contracts
- `read_file(path)`
- `search_code(query, glob, limit)`
- `run_tests(scope)`
- `apply_patch(path, patch)`
- `get_git_diff(base_ref)`

### Bad tool contracts
- `fix_bug(task)`
- `edit_repository(prompt)`
- `use_shell_for_anything(command_goal)`

Coding agents become unreliable when tools hide too much behavior.

## Verification Must Be First-Class

Never let the model be the final authority on whether a coding task succeeded.

After every material action, verify with evidence:
- tests actually passed
- build actually succeeded
- linter actually passed
- edited file exists and contains the expected change
- diff is limited to the intended scope
- new failures did not appear

### Coding-agent verification pattern
1. inspect repo
2. form hypothesis
3. make a small edit
4. run targeted verification
5. inspect outputs
6. either continue, revert, or try a new hypothesis

This loop is what separates a coding agent from a text generator.

## Memory and State for Coding Agents

Separate these clearly:
- **task state** — what bug/feature is being worked on
- **working memory** — hypotheses, failing test names, touched files
- **durable memory** — repo conventions, preferred commands, team policies
- **external context** — docs, issue tracker, CI logs, PR metadata

Do not dump all of this into one conversation history and call it memory.

## Practical Stack Guidance

### Best default for a custom coding agent
- Start with **Claude SDKs** or **OpenAI SDKs** directly.
- Implement a small repo loop first.
- Add OpenRouter only if you need portability or fallback.

### Best default for a repo-autonomous coding agent
- Evaluate **OpenHands** first.
- If you need deeper control over tool design or product embedding, build directly on Claude/OpenAI SDKs.

### Best default for multi-model experimentation
- Build your coding loop once.
- Put **OpenRouter** underneath it as the model backend.
- Re-test prompts, tools, and verification on every target model.

## Starter Templates

Use these as thin starting points, then narrow or extend the tools for your repo:

- `templates/python-coding-agent-starter.py`
- `templates/typescript-coding-agent-starter.ts`
- `templates/node-coding-agent-starter.js`

All three templates show the same basic pattern:
1. define narrow repo tools
2. call a model with those tools
3. inspect tool calls
4. dispatch tools locally
5. feed results back into the loop
6. verify with targeted commands

## Recommended Build Workflow

1. **Pick one coding task class**
   - bug fix, test repair, refactor, or review

2. **Implement the thinnest useful loop**
   - read relevant files
   - patch one file
   - run one verification command

3. **Keep edits narrow**
   - smaller diffs are easier to debug and verify

4. **Instrument everything**
   - log tool calls, stderr/stdout, changed files, and retries

5. **Test failure handling deliberately**
   - command failures
   - partial edits
   - malformed arguments
   - flaky tests
   - missing files

6. **Only then add scale features**
   - multiple agents
   - long-term memory
   - model fallback
   - broad tool surfaces

## Common Pitfalls

1. **Confusing model choice with coding-agent design**
   The model matters, but the repo loop matters more.

2. **Making edit tools too broad**
   Hidden side effects and huge diffs destroy reliability.

3. **Skipping targeted verification**
   If you do not run tests/build/lint after edits, the agent is guessing.

4. **Letting the agent run arbitrary shell commands too early**
   Start narrow, then expand permissions deliberately.

5. **Treating OpenHands like a normal SDK**
   It is a runtime/platform choice.

6. **Treating OpenRouter like the architecture**
   It is the model backend layer, not the coding loop.

7. **Overbuilding multi-agent setups before one agent works well**
   Make one bug-fixer reliable before adding reviewers, planners, or swarms.

8. **Using giant prompts to compensate for weak tools**
   Stable tools beat bloated prompts.

## Verification Checklist

- [ ] The coding-agent job is explicitly defined.
- [ ] The chosen stack matches the needed control level.
- [ ] Repo search, file read, edit, and verification tools are all present.
- [ ] Tools have narrow typed contracts.
- [ ] Edits are verified with tests, lint, build, or diff checks.
- [ ] State, working memory, and durable memory are separated.
- [ ] Logging/tracing exists for model calls and tool calls.
- [ ] Retry, timeout, and approval policies are explicit.
- [ ] The model/provider choice is based on coding workload requirements.
- [ ] Each provider/runtime assumption has been rechecked against current docs.
- [ ] The chosen starter template matches the target language/runtime.

## Reference Files

- `references/coding-agent-architecture.md`
- `references/claude-sdk.md`
- `references/openai-sdk.md`
- `references/openhands.md`
- `references/openhands-domain-monitor-pattern.md` — use when OpenHands should orchestrate a deterministic monitoring/notification app rather than serve as the core embedded SDK
- `references/openrouter.md`

## One-Shot Recipes

### Recipe: choose a stack for a new coding agent
1. Decide whether you need a product-embedded coding agent or a ready-made runtime.
2. If embedded, compare Claude SDKs vs OpenAI SDKs.
3. If runtime-first, evaluate OpenHands.
4. If multi-model portability matters, place OpenRouter under the chosen loop.
5. Implement one narrow repo-edit-and-verify slice before building memory or handoffs.

### Recipe: start from a template
1. Pick the closest starter template for your runtime.
2. Replace the generic tool contracts with repo-specific ones.
3. Narrow the verification command set.
4. Add diff inspection before declaring success.
5. Test on one bug-fix or test-repair task before broadening scope.

### Recipe: upgrade from prompt wrapper to coding agent
1. Replace freeform prompts with typed repo and execution tools.
2. Add a real edit-and-verify loop.
3. Add targeted tests/lint/build verification.
4. Add state compression for longer debugging sessions.
5. Add tracing and retry logic.
6. Only then add more tools or more agents.
