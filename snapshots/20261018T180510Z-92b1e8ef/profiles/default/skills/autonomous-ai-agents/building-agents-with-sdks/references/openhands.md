# OpenHands Reference

## Overview

OpenHands is best understood as an **agent runtime/platform for autonomous software engineering**, not as a classic importable SDK.

That distinction matters.

If Claude or OpenAI SDKs are tools you embed into your application, OpenHands is closer to a system you **configure, run, and operate** so an agent can work inside a repo or sandboxed environment.

This makes OpenHands especially relevant for coding-agent workflows, but only partially comparable to provider SDKs.

## Best Fit

Choose OpenHands when:
- You want a ready-made coding-agent runtime.
- You want an agent that can inspect repos, edit files, run commands, and iterate.
- You care more about getting a repo-operating agent working quickly than about building your own orchestration layer from scratch.
- You are comfortable with local/self-hosted/runtime-style setup.

Less ideal when:
- You want a small library to embed in your app.
- You need deep custom orchestration control at the SDK level.
- You are building a non-coding agent as the main use case.

## Core Primitives

The useful mental model is:
- **agent**
- **task/session**
- **workspace/runtime/sandbox**
- **model/provider configuration**
- **tool access**
- **repo-aware execution**
- **customization/instructions**

The important thing is that the runtime already owns much of the agent behavior.

## Best Architecture Pattern

Use OpenHands when you want:
- autonomous software engineering workflows
- an operational agent environment
- faster time to a working coding agent

Do not choose it if your real need is:
- a thin provider SDK
- a highly custom backend control loop
- tight product-embedded orchestration primitives

## Minimal Example Sketch

The most accurate “minimal example” is operational, not import-based:

1. Start OpenHands locally or self-hosted.
2. Configure a model/provider.
3. Open a repo or workspace.
4. Give it a task like:
   - fix failing tests
   - add a feature
   - investigate a bug
5. Review the resulting edits, commands, and outcomes.

That is closer to launching a coding-agent runtime than writing `import openhands` in an app.

## Python / TypeScript Implementation Guidance

Because OpenHands is not primarily an app-embedded SDK, the best “implementation example” for Python or TypeScript is usually **integration around the runtime**, not an in-process import.

### Python integration pattern
Use Python to:
- create or prepare a task payload
- launch or call the OpenHands runtime/service
- watch status
- fetch artifacts, logs, or resulting diffs
- run an external verification pass after the runtime finishes

Pseudo-shape:
```python
# Pseudocode only — verify current API/CLI surfaces in OpenHands docs.

task = {
    "repo": "/path/to/repo",
    "instruction": "Fix the failing API tests with the smallest safe patch.",
}

# submit task to OpenHands runtime
# poll session status
# fetch changed files / diff / logs
# run post-verification such as pytest or lint
```

### TypeScript integration pattern
Use TypeScript similarly when OpenHands is part of a larger devtooling platform:
```ts
// Pseudocode only — verify current API/CLI surfaces in OpenHands docs.
const task = {
  repo: "/path/to/repo",
  instruction: "Investigate the flaky worker tests and propose the smallest safe fix."
};

// submit task to OpenHands runtime
// poll or subscribe for updates
// fetch diff, logs, and completion result
// run external verification after completion
```

### Practical takeaway
If you want a **Python/TypeScript coding agent you own inside your app**, Claude/OpenAI SDKs are the more direct fit.
If you want a **runtime your Python/TypeScript system orchestrates from the outside**, OpenHands is the better framing.

## Concrete Integration Pattern for Domain Workflows

When a user asks to build something "with the OpenHands SDK" for a business workflow such as monitoring prices, checking external data, sending notifications, or supervising a repo-backed automation, do **not** force OpenHands into the role of an in-process library if the real need is operational orchestration.

Use this pattern instead:

1. Put the durable business logic in a normal app or CLI.
   - configuration parsing
   - provider/API calls
   - normalization
   - rule evaluation
   - notifications
   - persistence or dedupe
2. Use OpenHands as the runtime/operator around that app.
   - run the local scripts or commands
   - inspect outputs such as JSON reports, logs, or diffs
   - summarize results for the user
   - coordinate safe retries or follow-up actions
3. Encode hard constraints in multiple layers.
   - prompt/policy files
   - tool restrictions
   - code-level guardrails
   - credential scoping
4. Prefer a mock or stub provider first when live API credentials or scraping rules are unclear.
   - verify the control flow with deterministic test data
   - add live provider integrations only after checking current official docs

### Example: airfare monitor with "do not buy" policy
For a project that watches ATL -> CDG airfare and emails when the fare falls within a configured range:
- keep price fetching, threshold evaluation, cooldown logic, and email delivery in deterministic Python code
- let OpenHands run the check command, inspect the report, and summarize the result
- do not provide tools or credentials that could log in, enter passenger data, or submit payment
- include explicit policy docs in-repo so OpenHands is operating under reviewable written constraints

This pattern is usually more accurate than pretending OpenHands is the main embedded SDK for the product logic.

## Common Pitfalls

1. **Describing OpenHands as a normal SDK**
   This is the main conceptual mistake.

2. **Underestimating operational setup**
   Runtime, model config, permissions, and sandbox behavior all matter.

3. **Using it for the wrong workload**
   It is strongest for software engineering agents.

4. **Expecting deterministic outcomes without guardrails**
   Like other autonomous agents, it still needs review and boundaries.

5. **Ignoring credential and execution risk**
   Repo access and command execution need careful controls.

## Verification Checklist

- [ ] Reconfirm current official OpenHands positioning in docs.
- [ ] Recheck current install/runtime paths before documenting commands.
- [ ] Confirm current model/provider configuration surfaces.
- [ ] Confirm any GitHub/headless/automation integrations before citing them.
- [ ] Confirm how Python/TypeScript systems should interact with the runtime today.
- [ ] Keep the “runtime/platform, not primary SDK” disclaimer unless official docs clearly change.

## Official Links

- Docs: https://docs.all-hands.dev/
- GitHub: https://github.com/All-Hands-AI/OpenHands
- Site: https://www.all-hands.dev/

## Positioning Summary

Use OpenHands as an **adjacent coding-agent reference**: not the main low-level SDK path, but a strong option when the real goal is a ready-made autonomous coding-agent runtime.
