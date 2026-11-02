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

## Copilot-hosted Claude Sonnet 5 for native delegation

When the desired child model is `claude-sonnet-5` through GitHub Copilot, the ordinary Copilot provider route may default delegated children to the Responses API. That model can reject that transport even though a direct parent one-shot succeeds.

Use the explicit direct Copilot endpoint configuration below. The blank `api_key` is intentional: the delegated child inherits the authenticated Copilot credential from its parent rather than storing a duplicate secret.

```yaml
delegation:
  provider: copilot
  model: claude-sonnet-5
  base_url: https://api.githubcopilot.com
  api_mode: chat_completions
  api_key: ""
```

Why the endpoint override matters: `delegation.api_mode` is only applied by the delegation resolver when `delegation.base_url` is set. Without `base_url`, provider resolution may select the Copilot Responses transport regardless of the delegation-level override.

Validate it with a real child—not only a parent one-shot:

```bash
hermes chat -q "Use delegate_task exactly once. Its goal is: Reply with exactly CHILD_OK and nothing else. Then return only the child result." --toolsets delegation -Q
```

Expected child result: `CHILD_OK`.

## Anthropic/Claude subscription eligibility

A Claude Code login does **not** automatically make the native Hermes Anthropic provider usable. Hermes routes `delegation.provider=anthropic` through its own provider integration, which has separate subscription rules:

- **Claude Pro:** cannot use Hermes' native Anthropic OAuth route. Use Claude Code CLI as an externally orchestrated coding worker, or configure a billed Anthropic API key / another native provider for `delegate_task`.
- **Claude Max with purchased extra usage credits:** can authenticate through `hermes model` → Anthropic OAuth (or `hermes auth add anthropic --type oauth`). Hermes routes as Claude Code and consumes only the extra/overage credits; the base plan allowance is not used by Hermes.
- **Anthropic API key:** is pay-per-token and billed independently of any Claude subscription.

## Anthropic/Claude-specific pitfall

A common failure mode on macOS is:
- Claude Code CLI is logged in and appears healthy
- Hermes still cannot use `delegation.provider=anthropic`

Before treating this as a credential-refresh problem, check subscription eligibility above. For an eligible Max account, Hermes may detect Claude Code credentials from the macOS Keychain or `~/.claude/.credentials.json`; those credentials can still be expired or non-refreshable, so delegated children can fail even when `claude auth status` looks healthy.

### Diagnostic pattern
When an Anthropic child routing fails, check in this order:
1. Is the config split correct?
2. What subscription/API entitlement is intended?
3. Does `claude auth status --text` confirm the expected Claude Code account?
4. Does a minimal delegated child run through the intended credential route?

**Claude Pro is a decisive result:** native `delegate_task` via `provider: anthropic` cannot consume its included allowance, so re-login or `claude setup-token` will not make that route work. Use the Claude Code CLI worker path instead, configure another native child provider, or use a separately billed Anthropic API key.

For an eligible Claude Max account with extra credits, a failure after OAuth setup may be credential freshness/refreshability; then reauthenticate through `hermes model` and run a minimal child test.

### Practical recovery

Choose the path that matches the entitlement:

- **Claude Pro:** keep the subscription for `claude` CLI tasks (`claude -p` for bounded one-shot work or a tmux session for iterative work). This is Hermes-orchestrated external coding, not native `delegate_task` routing.
- **Claude Max + extra usage credits:** run `hermes model`, select **Anthropic OAuth**, complete browser authentication, restart Hermes, and rerun the child smoke test. Hermes will use refreshable Claude Code credentials where available.
- **Anthropic API billing:** set `ANTHROPIC_API_KEY` in `~/.hermes/.env`, restart Hermes/gateway, and rerun the child smoke test. This is pay-per-token and separate from a Claude subscription.

`claude setup-token` is a manual/legacy OAuth-token option. It does not convert a Claude Pro subscription into a supported native Hermes OAuth route. Never paste arbitrary tokens into `~/.hermes/.env`; use `hermes model` for the supported OAuth setup or a properly provisioned API key for API billing.

## Provider Availability and Fallback Routing

A configured key is not proof that a delegated provider is currently usable: account balance, subscription entitlement, quota, or provider-side access can still block child runs.

When a child lane fails while the parent lane works:
1. Report the condition concisely in user-facing terms; do **not** repeat raw vendor error text unless the user asks for it.
2. Inspect the persisted `delegation.provider`, `delegation.model`, and configured fallback list without exposing secret values.
3. Separate credential *presence* from provider *availability*. Do not diagnose a balance/quota/entitlement condition as a missing-key issue.
4. Offer a recovery path in priority order:
   - route delegation to the already-validated parent provider/model for immediate continuity;
   - configure and smoke-test another already-available provider/model as the dedicated child lane;
   - preserve the split and resolve the blocked provider account, then rerun a minimal child test.
5. Check `model.fallback_providers`; an empty list means no automatic failover is configured. Do not claim failover exists without a real child-run validation.

A safe diagnostic reports only credential presence (`SET`/`UNSET`) and non-secret routing values. Never print API keys, even while investigating availability.

## Reference material

- `references/split-gpt54-parent-sonnet46-child.md` — validated config shape, smoke-test commands, and the parent-works/child-fails Anthropic auth signature seen on macOS.
- `references/copilot-claude-protocol-routing.md` — direct Copilot endpoint protocol selection and source-of-truth child validation.

## Best practices

- Prefer encoding the split in `config.yaml`, not as an informal workflow the user must remember.
- Verify the parent path and child path separately.
- Treat parent success and child failure as a strong signal that the problem is auth, account availability, or routing for the delegated provider; distinguish these causes before changing models.
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
