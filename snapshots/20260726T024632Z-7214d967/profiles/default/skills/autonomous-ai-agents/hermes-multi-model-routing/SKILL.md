---
name: hermes-multi-model-routing
description: Configure Hermes to use one model/provider for orchestration and a different model/provider for delegation/coding lanes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, routing, models, providers, delegation, anthropic, copilot, coding]
    related_skills: [hermes-agent, claude-code, codex]
created_by: agent
---

# Hermes Multi-Model Routing

Use this skill when the user wants Hermes to run a **split-brain model setup**:
- one model/provider for the main conversation and orchestration loop
- a different model/provider for delegated coding work

Typical example:
- **parent/orchestration:** GPT-5.4 via GitHub Copilot
- **delegation/coding lane:** Claude Sonnet 4.6 via Anthropic

This is a class-level setup pattern for long-term Hermes operation, not a one-off interview trick.

## When to use

Use this skill when the user asks to:
- route Hermes planning/orchestration to one model and coding to another
- configure `delegate_task` children differently from the parent model
- keep Hermes parent on Copilot/OpenAI while pinning subagents to Anthropic Claude
- make a long-term, repeatable model/provider split in Hermes config

## Core idea

Hermes supports separate routing for:
- `model.*` → the main agent session
- `delegation.*` → child agents created by `delegate_task`

The clean long-term pattern is:
1. pin the parent model/provider under `model`
2. pin the coding lane under `delegation`
3. verify the parent path independently from the child path
4. if child routing fails, debug credentials separately from config

## Recommended workflow

### 1. Inspect the current live state
Check both the effective runtime and the persistent config.

Key commands:
```bash
hermes status --all
hermes config
hermes config path
```

Do not assume the current provider from memory. Verify it live.

### 2. Apply the parent/orchestration route
Example:
```bash
hermes config set model.default gpt-5.4
hermes config set model.provider copilot
```

If the provider requires a specific base URL, verify whether Hermes already manages it or whether it is present in config.

### 3. Apply the child/delegation route
Example:
```bash
hermes config set delegation.provider anthropic
hermes config set delegation.model claude-sonnet-4-6
```

This is the Hermes-native way to separate orchestration from delegated coding.

### 4. Validate parent and child independently
Validate the parent with a plain one-shot query:
```bash
hermes chat -q 'Reply with exactly PARENT_OK and nothing else.' -Q
```

Validate child routing with a minimal delegation call:
```bash
hermes chat -q "Use delegate_task once with goal: reply with exactly CHILD_OK and nothing else. Then return only the child result text." --toolsets delegation -Q
```

Interpret failures carefully:
- parent succeeds + child fails → routing or child credentials issue
- both fail → broader provider/config issue

## Anthropic/Claude-specific pitfall

A common failure mode on macOS is:
- Claude Code CLI is logged in and appears healthy
- Hermes still cannot use `delegation.provider=anthropic`

Why this happens:
- Hermes may detect Claude Code credentials from the macOS Keychain or `~/.claude/.credentials.json`
- those credentials can be **expired**
- Hermes may be unable to refresh them successfully
- result: delegated Anthropic children fail even though `claude auth status` looks fine

### Diagnostic pattern
When Anthropic child routing fails, separate these checks:
1. Is the config split correct?
2. Does `claude auth status --text` show a valid Claude account login?
3. Does Hermes status still report Anthropic as not configured?
4. Does a minimal delegated child fail with a provider credential error?

If yes, the issue is usually **credential freshness/refreshability**, not the config shape.

### Practical recovery

Prefer the direct Hermes credential path for `delegation.provider=anthropic`:

```bash
# Add this to ~/.hermes/.env, then restart Hermes/gateway.
ANTHROPIC_API_KEY=sk-ant-...
```

ANTHROPIC_API_KEY=sk-ant-...
```

Then restart Hermes/gateway and re-run the minimal delegated child validation command above.

`claude setup-token` is different: it configures Claude Code's own long-lived auth token and normally writes/updates Claude Code auth state. Do **not** paste its output into `~/.hermes/.env` unless the command explicitly gives an Anthropic API key and instructs you to export it. Use it only when you intentionally want Hermes to try consuming Claude Code OAuth/subscription credentials indirectly:

```bash
claude setup-token
```

If that is not enough, retry full Claude auth:

```bash
claude auth login
```

If delegated Hermes children still report missing Anthropic credentials after Claude Code reauth, set `ANTHROPIC_API_KEY` in `~/.hermes/.env`; that is the least ambiguous fix.

## Reference material

- `references/split-gpt54-parent-sonnet46-child.md` — validated config shape, smoke-test commands, and the parent-works/child-fails Anthropic auth signature seen on macOS.

## Best practices

- Prefer encoding the split in `config.yaml`, not as an informal workflow the user must remember.
- Verify the parent path and child path separately.
- Treat parent success and child failure as a strong signal that the problem is auth for the delegated provider.
- Keep the orchestration model stable unless the user explicitly wants both layers changed.
- For long-term maintenance, document the intended split in a skill or project notes so future sessions do not collapse back to a single-model assumption.

## Pitfalls

- Do not assume a logged-in Claude Code CLI automatically means Hermes direct Anthropic routing will work.
- Do not conflate `claude` CLI usability with Hermes `delegate_task` credential readiness.
- Do not stop after setting `delegation.provider` and `delegation.model`; always test a real child run.
- Do not diagnose child-model failures as model-name problems until provider auth has been ruled out.

## Output to the user

When reporting results, separate:
1. config state
2. parent validation result
3. child validation result
4. minimal next step if credentials still block delegated routing

A good final summary looks like:
- parent/orchestration configured and working
- delegation/coding lane configured
- delegated lane operational or blocked
- if blocked, exact auth remediation step
