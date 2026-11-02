# Copilot Claude Models: Delegation Protocol Routing

## Problem shape

A model can pass a direct Copilot parent-session preflight yet fail as a native Hermes child because the provider chooses a different wire protocol for delegation.

Example observed in July 2026:

- Parent preflight: `copilot` + `claude-sonnet-5` returned a successful one-shot response.
- Native child: the default Copilot delegated route selected the Responses transport.
- The Claude model rejected that transport and required Chat Completions.

Do not infer child compatibility from a parent-only preflight.

## Why `delegation.api_mode` may appear ineffective

Hermes applies `delegation.api_mode` directly when delegation uses a configured `delegation.base_url`. With only `delegation.provider: copilot`, runtime provider resolution selects Copilot's model-specific default transport and can override the delegated `api_mode` setting.

## Direct Copilot endpoint pattern

When the model requires Chat Completions, use the Copilot endpoint explicitly and retain provider credentials through inheritance:

```yaml
delegation:
  provider: copilot
  model: claude-sonnet-5
  base_url: https://api.githubcopilot.com
  api_mode: chat_completions
  api_key: ""  # leave blank; inherit the authenticated parent Copilot credential
```

This is a protocol-routing configuration, not a stored-token workaround. Never copy a Copilot credential into `delegation.api_key` merely to make this work.

## Validation sequence

1. Preflight the exact model via Copilot in a one-shot request.
2. Persist the `delegation` route, including `base_url` and `api_mode` where required.
3. Invoke a real `delegate_task` child—not only a parent prompt that claims to relay child output.
4. Confirm the child returns its sentinel result and no protocol error.
5. If the child fails, retain the error category and the selected provider/model/protocol, but do not expose tokens or raw credential values.

A parent wrapper can produce an incomplete or misleading final response even if it launched a child. The native child result is the source of truth.

## Re-review triggers

Revalidate this pattern whenever Hermes changes delegation routing, Copilot changes model availability/protocol support, or the delegated model changes.
