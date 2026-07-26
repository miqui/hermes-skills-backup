# AI SDK tool streaming pitfalls in text-first chat scaffolds

Use this when extending an existing AI SDK chat app where the current UI renders only text parts.

## Main pitfall
A multi-step tool call can succeed while the assistant emits no final visible text. In a text-only renderer, that looks like a blank assistant turn even though tool results exist.

## Durable route-level pattern
1. Keep the fix in the existing chat route before changing UI components.
2. Merge the model UI stream with `sendFinish: false`.
3. Await the completed `streamText(...)` result fields you need (for example `text`, `toolResults`, `finishReason`).
4. If final assistant text is empty but tool results exist, write a fallback plain-text assistant summary from the most relevant tool result `summary`.
5. Emit one outer UI `finish` chunk yourself.

## Important typing note
Do not assume lower-level stream finish metadata is legal on UI finish chunks.
In this session, the local AI SDK UI writer accepted `finishReason` on `writer.write({ type: "finish", ... })`, but not `rawFinishReason` or `totalUsage`.
Always verify the installed SDK types in `node_modules/ai/dist/index.d.ts` before writing custom finish events.

## Tool-budget pattern
If you use `prepareStep` plus `activeTools` to prevent runaway tool loops:
- disable tools only after at least one tool step has been used
- when tools are disabled, override the step/system instruction so the model must answer in plain text from confirmed tool results already in context

## Route-only scope discipline
When a phased plan says “route only”:
- keep shaping helpers local to the route when they are orchestration-specific
- do not expand domain modules just to satisfy one orchestration step unless the new behavior is clearly reusable
- for category -> items expansion, use the authoritative in-repo catalog directly if the existing helper layer does not yet expose that exact seam

## Validation checklist
- TypeScript compile passes after custom stream edits
- No duplicate finish event
- No missing finish event
- Tool-only turn still produces visible assistant text
- Existing `onFinish` persistence path remains intact
