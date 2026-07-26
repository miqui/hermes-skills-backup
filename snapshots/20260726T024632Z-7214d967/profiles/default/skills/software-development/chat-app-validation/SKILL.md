---
name: chat-app-validation
description: Validate local AI/chat web apps end-to-end by separating runtime setup, direct API probing, browser UX checks, and tool-result rendering verification.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [chat, validation, browser, ai-sdk, tool-calling, qa]
    related_skills: [dogfood, playwright-testing]
---

# Chat App Validation

## When to use
Use this when validating a local chat or agent web app, especially when it uses streamed responses, tool-calling, local databases, and browser-rendered assistant messages.

Typical triggers:
- "validate the local flow end-to-end"
- "exercise the chat UI locally"
- "why does the browser show less than the API stream?"
- "the tool ran but the user only sees a preamble"

## Goals
1. Prove the local app can boot with the required runtime configuration.
2. Separate server/API correctness from browser/hydration/rendering issues.
3. Verify visible user outcomes, not just successful tool execution.
4. Detect multi-intent orchestration gaps that only appear in live chat turns.

## Workflow

### 1) Ground the runtime before UI testing
- Confirm the app's expected env vars and local DB config from the repo docs/config examples.
- Prefer repo-local ignored env files (for example `.env.local`) for validation-only settings.
- Run migrations before launching the app if the project uses Prisma or another local DB layer.
- Start the app in a tracked background process so logs remain inspectable.

### 2) Use `localhost` for Next.js dev validation
- For Next.js dev servers, prefer `http://localhost:<port>` over `http://127.0.0.1:<port>` when using browser automation.
- If the page loads but submit/hydration behavior is strange, suspect dev-origin resource blocking or hydration mismatch before assuming the app logic is wrong.
- Re-test on `localhost` before patching UI code.

### 3) Prove the server path separately from the browser path
- Hit the page in a browser and check console/runtime errors.
- Also POST directly to the chat/API route with a valid payload.
- If the API works but the browser does not, focus on hydration, form wiring, stream persistence, or message rendering.
- If both fail, focus on runtime env, model/provider setup, or backend route logic.

### 4) Inspect the actual stream shape
When the browser shows an incomplete answer:
- Read the streamed event sequence.
- Check whether the model emitted:
  - preamble text,
  - tool input/output,
  - `finishReason`, especially `tool-calls`.
- Distinguish these cases:
  1. No visible assistant text and tool results exist.
  2. Only a short preamble is visible, but tool results contain the real answer.
  3. Tool results are present in the stream but lost before rendering/persistence.

### 5) Validate rendered outcomes, not just backend success
For tool-calling chat apps, verify that the browser visibly shows:
- menu/search/category results
- cart/order summaries
- confirmation IDs / totals / status text

A `200` API response is not enough if the user only sees the preamble.

### 6) Exercise both sequential and combined intents
Run both:
- sequential single-operation turns
- combined multi-intent turns like "show cart, then update quantity"

If single-step turns work but combined turns stop after the first action, record that as an orchestration limitation rather than a total flow failure.

### 7) Promote stable flows to Playwright regressions
After the local browser/API path is understood, use `playwright-testing` when the flow should be repeatable in development or CI.

Promote these cases:
- a manually reproduced rendering bug
- a tool-result card or action that must not regress
- an auth, checkout, ordering, or multi-step chat journey
- a browser/API mismatch that was fixed and needs guardrails

Keep one-off exploratory notes in the validation report; encode durable user-visible behavior as Playwright E2E tests.

## Common fixes

### Tool-backed turn ends with `finishReason: "tool-calls"`
If the browser only shows a preamble (for example, "Let me look that up for you!") but tool results contain the real summary:
- inspect the route's fallback summary logic
- ensure the fallback runs not only when final visible text is empty, but also when the turn ended on `tool-calls` after tool results were produced
- then re-test in the real browser, not just the direct API probe

### Runtime env looks present in shell but missing in app
- Check the env file actually loaded by the framework.
- Restart the dev server after env changes.
- Verify without printing secrets.

## Pitfalls
- Do not trust `127.0.0.1` and `localhost` to behave identically in Next.js dev browser validation.
- Do not conclude the UI is correct just because streamed tool output exists at the API layer.
- Do not treat a multi-intent failure as proof the whole ordering/cart flow is broken if sequential turns pass.
- Do not expose secrets while checking env presence.
- Do not stop at manual validation for flows that are critical or previously broken; hand those to `playwright-testing` as repeatable regressions.

## Outputs to provide
- exact validation scope
- what passed in browser
- what only passed at API layer
- known remaining limitations
- PR/checkpoint link if changes were required

## References
- `playwright-testing` — use after manual/API validation when a stable chat/browser flow should become repeatable E2E regression coverage.
- `references/nextjs-ai-sdk-local-validation.md` — condensed notes from a real local validation/debugging session covering localhost vs 127.0.0.1, env loading, stream inspection, and tool-call fallback rendering.
