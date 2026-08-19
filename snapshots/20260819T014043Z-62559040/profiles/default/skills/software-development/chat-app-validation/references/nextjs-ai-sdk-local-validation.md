# Next.js + AI SDK local validation notes

Condensed from a real local restaurant-ordering chat validation session.

## Durable takeaways

### 1) Prefer `localhost` over `127.0.0.1` for Next dev browser automation
In this session, the app appeared to load on `127.0.0.1:3000`, but browser interaction behaved incorrectly:
- submits navigated oddly
- hydration/JS behavior looked broken
- chat actions were not representative of the actual app

Switching validation to `http://localhost:3000` resolved the dev-origin behavior and allowed reliable UI testing.

Use this as an early diagnostic branch before changing frontend code.

### 2) Separate API health from browser rendering
Direct POSTs to `/api/chat` showed the streamed events were richer than the browser-visible output.
This distinguished:
- backend/tool execution working
- browser rendering/persistence being incomplete

Useful probe pattern:
- browser check for visible outcome
- direct API POST for raw stream
- compare the two before deciding where the bug lives

### 3) Tool-result fallback may need to handle `finishReason: "tool-calls"`
Observed stream pattern:
- model emits a short preamble text
- tool output contains the real answer/summary
- stream ends with `finishReason: "tool-calls"`

If fallback text is only appended when final text is empty, the user can end up seeing only the preamble.

Minimal safe fix used in this session:
- broaden fallback injection from:
  - `finalText.trim().length === 0 && finalToolResults.length > 0`
- to:
  - `finalToolResults.length > 0 && (finalText.trim().length === 0 || finishReason === "tool-calls")`

This preserves text-first rendering while making tool-backed summaries visible.

### 4) Validate sequential and multi-intent turns separately
Observed behavior:
- single-step turns worked reliably:
  - add item
  - read cart
  - update quantity
  - remove item
  - submit order
- some combined requests only executed the first operation:
  - read + update
  - add + submit

Conclusion pattern:
- sequential end-to-end flow can pass
- multi-intent orchestration can still be a known limitation

Report both explicitly rather than collapsing them into a single pass/fail verdict.

### 5) Verify env presence without printing secrets
Safe check pattern:
- verify whether required keys are set/present
- do not print their values
- restart the dev server after changing `.env.local`

## Good final report shape
- runtime prerequisites applied
- direct API result
- browser-visible result
- fixes made
- known remaining limitations
- checkpoint/PR link if applicable
