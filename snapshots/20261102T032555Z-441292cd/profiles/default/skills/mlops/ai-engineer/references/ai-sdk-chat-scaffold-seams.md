# AI SDK Chat Scaffold Seams

Use this note when analyzing an existing AI SDK chat application before proposing changes.

## Goal

Identify the **lowest-friction extension seams** in an existing chat scaffold instead of inventing a parallel architecture.

## Primary seam order

1. **Client transport seam**
   - Locate `useChat(...)`.
   - Record request shape and transport (`DefaultChatTransport` or equivalent).
   - Confirm whether the client already consumes structured `messages` with `parts`.

2. **Server orchestration seam**
   - Locate the route using `streamText`, `generateText`, `createUIMessageStream`, or `createUIMessageStreamResponse`.
   - This is typically the correct insertion point for AI SDK `tools`.
   - Prefer extending this route over creating separate AI endpoints that bypass the SDK stream protocol.

3. **Message rendering seam**
   - Locate the assistant message renderer.
   - Check whether it only renders `part.type === "text"`.
   - If so, add switching for typed tool parts such as `tool-<toolName>` there.

4. **Persistence seam**
   - Locate serialization/deserialization of chat messages.
   - If message `parts` are already persisted as JSON and reconstructed into `UIMessage`/`UIMessagePart`, tool parts can usually reuse the same pipeline.

5. **Business state seam**
   - Check whether the app currently persists only chat history.
   - If the feature requires mutable domain state (cart, order, workflow state, approval state), add separate domain models; do not treat the conversation transcript as the source of truth.

## Practical defaults

### Prefer server-side tools when
- Reading local files or server-side resources
- Querying or mutating authoritative app state
- Writing orders, carts, workflows, or database records
- You want predictable, audit-friendly behavior in the same server route

### Prefer client-side tools when
- Accessing browser-only APIs
- Requiring direct user interaction or confirmation
- Reading device-local context unavailable on the server

## AI SDK UI facts worth remembering

- Tool calls are generated during `streamText(...)`.
- Tool calls and results are forwarded through the UI message stream.
- The client sees them as typed parts in assistant `message.parts`.
- Tool-specific UI should render from those parts, not from parsing assistant prose.

## Good output shape for architecture guidance

Summarize findings as:
- current chat path
- current rendering path
- current persistence path
- missing domain state
- cleanest insertion seam for tools
- cleanest insertion seam for UI cards/components

## Assessment / audited repo reminder

When the repo includes evaluation harness instructions (`AGENTS.md`, `README`, `Makefile` install/submit targets), call them out explicitly in the repo briefing so implementation advice respects the repo's workflow and scoring model.
