---
name: vercel-ai-sdk
description: Use when writing or migrating TypeScript code with the Vercel AI SDK (`ai` pkg). Covers generateText/streamText, Output structured data, tools, agents, useChat, AI Gateway, and v5→v6→v7 pitfalls.
version: 1.0.0
tags: [vercel, ai-sdk, typescript, llm, streaming, agents, ai-gateway]
---

# Vercel AI SDK (TypeScript)

Current major (docs fetched 2026-10-28): **AI SDK 7** (`ai@^7`, 7.0.x patch releases; ESM-only, Node 22+). v6 → v7 guide exists; v5 → v6 guide exists. Code below is **UNVERIFIED** (not executed) — copied/adapted from current docs. Always check installed version first: `npm ls ai @ai-sdk/react`.

## Install
```
pnpm add ai @ai-sdk/react zod      # add @ai-sdk/openai etc. only if bypassing the Gateway
```
Provider packages track the core major (v6: `@ai-sdk/*@^3`; check v7 pins in the migration guide).

## Models: plain strings via AI Gateway
A `"provider/model"` string routes through Vercel AI Gateway; no provider import needed.
```ts
import { generateText } from 'ai';
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-5.5',
  instructions: 'Be terse.',        // v7: was `system`
  prompt: 'Explain AI Gateway in one sentence.',
});
```
Direct provider (BYO key): `import { openai } from '@ai-sdk/openai'; model: openai('<id>')`. Model IDs change often — browse https://vercel.com/ai-gateway/models rather than guessing.

## Auth / env
- Gateway: set `AI_GATEWAY_API_KEY` (any host), or on Vercel deployments use OIDC (`vercel env pull` / `vercel link` populates a token for local dev). Never hardcode or commit keys; keep in `.env.local`.
- BYOK, budgets, provider ordering/fallbacks, request logs: configured in Vercel dashboard / `providerOptions.gateway` (see Gateway docs).
- Direct providers read their own env vars (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- Gateway also exposes OpenAI-compatible `https://ai-gateway.vercel.sh/v1/chat/completions` with `Authorization: Bearer $AI_GATEWAY_API_KEY`.

## Structured output (CURRENT API: `output` + `Output.*`)
`generateObject`/`streamObject` are **deprecated** (since v6). Use:
```ts
import { generateText, Output } from 'ai';
import { z } from 'zod';
const { output } = await generateText({
  model: 'anthropic/claude-sonnet-5.5',
  output: Output.object({ schema: z.object({ name: z.string(), steps: z.array(z.string()) }) }),
  prompt: 'Generate a lasagna recipe.',
});
```
- Variants: `Output.text()` (default), `Output.object({schema})`, `Output.array({element,minItems,maxItems})`, plus choice/json variants — check docs.
- Streaming: `streamText({ output: Output.object(...) })` → iterate `partialOutputStream` (partials are NOT schema-validated) or `elementStream` for arrays.
- `experimental_output` was removed in v7 → `output`.
- Errors: `NoObjectGeneratedError` (parse/validate failure; has `.text`, `.cause`); `NoOutputGeneratedError` when reading `result.output` after a final step that ended with `tool-calls`. `output` is a getter, so destructuring can throw.
- Output generation counts as a step: with tools, set `stopWhen` high enough (e.g. `isStepCount(5)`).
- Client side: `useObject` hook.

## Tools
```ts
import { generateText, tool, isStepCount } from 'ai';
import { z } from 'zod';
const result = await generateText({
  model: 'anthropic/claude-sonnet-5.5',
  tools: {
    weather: tool({
      description: 'Get the weather in a location',
      inputSchema: z.object({ location: z.string() }),   // NOT `parameters`
      execute: async ({ location }) => ({ location, temperature: 72 }),
    }),
  },
  stopWhen: isStepCount(5),
  prompt: 'Weather in San Francisco?',
});
```
- `inputSchema` (v5+), results are `output` (not `result`) in UI parts.
- `execute` optional: omitting it forwards the call to client/queue and stops the loop.
- Approval: use `toolApproval` on generateText/streamText/ToolLoopAgent; `needsApproval` on `tool()` is deprecated. Statuses: `'not-applicable' | 'approved' | 'denied' | 'user-approval'`.
- `strict: true` per tool (provider-dependent); `activeTools` limits tools per step; `toolChoice` forces selection.
- Per-tool context: `contextSchema` + `toolsContext: { toolName: {...} }`; shared data via `runtimeContext` (v7; was `experimental_context`).
- `toModelOutput({ output })` takes an object param (v6+). Media results use `type: 'file'` (v7; `image-*`/`file-*`/`media` deprecated).

## Agents / loops
Default for plain `generateText`/`streamText` is **one step** unless `stopWhen` is set. `ToolLoopAgent` defaults to 20 steps.
```ts
import { ToolLoopAgent, isStepCount } from 'ai';
const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-5.5',
  instructions: 'You are a support agent.',
  tools: { /* ... */ },
  stopWhen: isStepCount(10),          // explicit; avoids default-limit warning
});
const r = await agent.generate({ prompt: 'Where is order 42?' });
```
Loop ends when: finish reason isn't `tool-calls`, a called tool has no `execute`, a call needs approval, or a stop condition hits. `prepareStep` (was `experimental_prepareStep`) can change `instructions`/tools/model per step. Route Handler: `createAgentUIStreamResponse({ agent, uiMessages: messages, abortSignal: request.signal })`.

## Streaming Route Handler + useChat
```ts
// app/api/chat/route.ts
import { convertToModelMessages, createUIMessageStreamResponse, streamText, toUIMessageStream, type UIMessage } from 'ai';
export const maxDuration = 30;
export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: 'anthropic/claude-sonnet-5.5',
    instructions: 'You are a helpful assistant.',
    messages: await convertToModelMessages(messages),   // async since v6
  });
  return createUIMessageStreamResponse({ stream: toUIMessageStream({ stream: result.stream }) });
}
```
```tsx
'use client';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';
export default function Page() {
  const { messages, sendMessage, status } = useChat({ transport: new DefaultChatTransport({ api: '/api/chat' }) });
  const [input, setInput] = useState('');
  return (<>
    {messages.map(m => <div key={m.id}>{m.parts.map((p, i) => p.type === 'text' ? <span key={i}>{p.text}</span> : null)}</div>)}
    <form onSubmit={e => { e.preventDefault(); if (input.trim()) { sendMessage({ text: input }); setInput(''); } }}>
      <input value={input} onChange={e => setInput(e.target.value)} disabled={status !== 'ready'} />
    </form></>);
}
```
- `useChat` no longer manages `input`/`handleSubmit`; keep your own state and call `sendMessage({ text })`. Status: `submitted | streaming | ready | error`.
- Render `message.parts` (text, tool parts, reasoning), not `message.content`.
- Type tools end-to-end: `InferUITools<typeof tools>` → `UIMessage<never, UIDataTypes, MyUITools>` → `useChat<MyUIMessage>()`.
- Plain text stream: `createTextStreamResponse({ stream: toTextStream({ stream: result.stream }) })`.
- Node/Express: `pipeUIMessageStreamToResponse({ stream, response })`.
- `streamText` errors go into the stream, not thrown — pass `onError`. v7 adds `streamRetries` and `toolCallConcurrency`.

## Version-migration pitfalls (check which major the repo is on)
| Old | Current |
|---|---|
| `generateObject` / `streamObject` (deprecated v6) | `generateText`/`streamText` + `output: Output.object(...)`; `partialObjectStream`→`partialOutputStream`; result `.object`→`.output` |
| `Experimental_Agent`, `system` | `ToolLoopAgent`, `instructions` |
| `system` (v7) | `instructions` (also in `prepareStep`) |
| `stepCountIs` (v6) | `isStepCount` (v7 codemod `rename-step-count-is`) |
| `result.fullStream` (v6) | `result.stream` (v7) |
| `result.toUIMessageStreamResponse()`, `toTextStreamResponse()`, `pipe*` methods | stateless helpers: `toUIMessageStream`, `createUIMessageStreamResponse`, `toTextStream`, `createTextStreamResponse` (methods deprecated in v7) |
| `onStepFinish` / `onFinish` | `onStepEnd` / `onEnd` (v7); `onEnd.usage` is now all steps, `totalUsage` deprecated |
| `experimental_telemetry`, `experimental_context` | `telemetry`; `runtimeContext` / per-tool `context` |
| `includeRawChunks` | `include: { rawChunks: true }` |
| `result.reasoningText/response/providerMetadata` (top-level) | `result.finalStep.*`; top-level `toolCalls/files/content` now aggregate ALL steps |
| `convertToCoreMessages`, `CoreMessage` (removed v6) | `await convertToModelMessages`, `ModelMessage` |
| `parameters`, `maxSteps`, `toolInvocations`, `useChat` `input/handleSubmit/append` (v4) | `inputSchema`, `stopWhen`, `parts`, `sendMessage` |
| `textEmbeddingModel` | `embeddingModel` |
| `ToolCallOptions` | `ToolExecutionOptions` |
| user part `{type:'image'}` | `{type:'file', data, mediaType:'image/png'}` |
| Mock*V2 (`ai/test`) | Mock*V3 (v6) |
| `experimental_transcribe/generateSpeech/generateImage` | `transcribe`/`generateSpeech`/`generateImage` |
| UI helpers `isToolUIPart`/`getToolName` (v5 meaning) | v6: `isStaticToolUIPart`/`getStaticToolName`; `isToolUIPart`/`getToolName` now include dynamic tools |
Provider notes: OpenAI `strictJsonSchema` defaults true (v6); Azure default uses Responses API; Vertex metadata key `vertex` not `google`; Google renames `GoogleGenerativeAI*`→`Google*` (`createGoogle`); `xai(id)` uses Responses API in v7 (`xai.chat()` for old).

Migrate with codemods, then fix remainder by hand and run `tsc`:
```
npx @ai-sdk/codemod v6    # v5 -> v6
npx @ai-sdk/codemod v7    # v6 -> v7
```
(Do NOT run `upgrade`; it replays all versions.) Vercel also ships a skill: `npx skills add vercel/ai --skill migrate-ai-sdk-v6-to-v7`.

## Other pitfalls
- Training-data-era snippets (v4/v5) are everywhere: `maxSteps`, `toDataStreamResponse`, `parameters`, `result.toolInvocations`, `useChat({ api })`. Treat as stale.
- Don't `await` `streamText(...)` itself; it returns synchronously. Consume `result.stream`/`textStream`, or await `result.text` / `result.finalStep` promises.
- With tools + `Output`, the final step must finish with `stop` or `.output` throws.
- Zod: AI SDK accepts Zod, Valibot, or `jsonSchema()`; match the Zod major the installed `ai` supports.
- Set `maxDuration` on Vercel Route Handlers for long generations; forward `req.signal` as `abortSignal`.
- Gateway model strings are unverified at runtime — a typo yields a gateway error, not a TS error.

## Sources (fetched 2026-10-28)
- https://ai-sdk.dev/docs/introduction
- https://ai-sdk.dev/docs/migration-guides/migration-guide-7-0
- https://ai-sdk.dev/docs/migration-guides/migration-guide-6-0
- https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data
- https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling
- https://ai-sdk.dev/docs/ai-sdk-ui/chatbot
- https://ai-sdk.dev/docs/reference/ai-sdk-core/generate-text
- https://v6.ai-sdk.dev/docs/agents/building-agents (legacy v6 docs)
- https://vercel.com/docs/ai-gateway
- UNVERIFIED (no official source checked): v7 release cadence and `createAgentUIStreamResponse`.
- Not fetched/verified: exact v7 provider package versions, Gateway OIDC local-dev steps, `providerOptions.gateway` fields.
