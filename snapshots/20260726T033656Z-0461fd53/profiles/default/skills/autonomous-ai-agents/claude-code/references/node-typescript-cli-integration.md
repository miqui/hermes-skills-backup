# Node/TypeScript Claude Code Integration

Use this reference when a Node or TypeScript application needs to invoke Claude Code as part of an app workflow rather than as a human-run terminal session.

## Key Finding

Do not assume the npm package `@anthropic-ai/claude-code` exposes a stable importable JavaScript SDK surface for app code.

In this environment, installing `@anthropic-ai/claude-code` provided the Claude CLI and platform binary, but not a directly usable `query()` import for the app runtime. For app integration, verify the actual package exports before designing around imports shown in high-level docs.

## Safe Integration Pattern

When the package behaves as a CLI wrapper, invoke Claude through a small typed helper around `child_process.spawn`.

Recommended command pattern:

```bash
claude -p --output-format json <prompt>
```

Common app-friendly variant:

```bash
<command> <args...> -p --output-format json <prompt>
```

Examples:

```bash
npx claude -p --output-format json "Write a 2-sentence BTC price alert as JSON"
claude -p --output-format json "Summarize this diff"
```

## What to Parse

For `--output-format json`, parse the final JSON object and read the `result` field. Treat missing/empty `result` as failure.

Typical shape:

```json
{
  "type": "result",
  "subtype": "success",
  "result": "...",
  "session_id": "..."
}
```

## App Integration Guidance

- Keep Claude invocation behind an adapter such as `query(options)`.
- Make the command and args env-configurable for portability, e.g. `CLAUDE_COMMAND`, `CLAUDE_ARGS`.
- Add a timeout and kill the subprocess on expiry.
- Capture both stdout and stderr; include stderr in failure messages.
- Validate the Claude response before using it in downstream actions like email sending.
- Provide a deterministic fallback path if Claude is unavailable, unauthenticated, times out, or returns malformed output.

## Good Fit

This pattern is appropriate when Claude is one step inside a larger workflow, for example:
- composing an email body
- summarizing an API response
- generating a short notification
- classifying or extracting structured text

## Notable Pitfall

If the user asks for a TypeScript app using the Claude Agent SDK, do not blindly promise a direct `import { query } ...` integration. First verify whether the installed package actually exports that API in the target environment.
