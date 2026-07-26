# Hermes multi-model routing — validated pattern

## Verified config shape

```yaml
model:
  default: gpt-5.4
  provider: copilot
  base_url: https://api.githubcopilot.com

delegation:
  provider: anthropic
  model: claude-sonnet-4-6
```

## Validation commands

### Parent / orchestration
```bash
hermes status --all
hermes chat -q 'Reply with exactly PARENT_OK and nothing else.' -Q
```

Expected outcome:
- status shows `Model: gpt-5.4`
- status shows `Provider: GitHub Copilot`
- one-shot query succeeds

### Child / delegated coding lane
```bash
hermes chat -q "Use delegate_task once with goal: reply with exactly CHILD_OK and nothing else. Then return only the child result text." --toolsets delegation -Q
```

Expected outcome:
- successful delegated child response

## Observed failure signature

When parent works but child fails with:

```text
delegate_task failed: Cannot resolve delegation provider 'anthropic' (no credentials configured).
```

that indicates:
- config split is present
- parent routing is fine
- delegated Anthropic auth is the remaining blocker

## Claude/Anthropic auth nuance on macOS

Hermes can read Claude Code credentials from:
- macOS Keychain service `Claude Code-credentials`
- `~/.claude/.credentials.json`

A logged-in Claude Code CLI is not sufficient by itself.

The important distinction is:
- `claude auth status --text` can look healthy
- Hermes can still fail if the underlying OAuth credential is expired and not refreshable

## Minimal remediation sequence

Try:

```bash
claude setup-token
```

If that is not enough, retry full Claude auth:

```bash
claude auth login
```

Then rerun the delegated-child validation command.
