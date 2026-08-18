# Chat tool-result card validation

Use this reference when dogfooding AI/chat applications that render tool results as inline UI cards (for example menu, cart, or checkout cards produced from AI SDK tool parts or MCP Apps-style tool outputs).

## What to verify

- Tool result parts render as structured UI, not only assistant prose.
- Each required tool-output class has a visible card state (for example item detail, collection/category, cart review, confirmation/result).
- Card buttons are real affordances and trigger the expected application flow through the normal UI path.
- Unavailable or invalid actions are visibly disabled when appropriate.
- Text fallback remains present enough that chat history is understandable if custom card rendering fails.
- Browser console remains clean after navigation, rendering, and each card interaction.

## Practical browser workflow

1. Start from a fresh chat/session where possible so prior messages do not confuse the DOM.
2. Ask for a tool-result that should produce a specific card.
3. Inspect the rendered DOM for card text and controls:
   ```js
   (() => ({
     text: document.body.innerText,
     buttons: Array.from(document.querySelectorAll('button')).map((b, i) => ({
       i,
       text: b.innerText || b.getAttribute('aria-label') || '',
       disabled: b.disabled,
     })),
   }))()
   ```
4. Click at least one card action and confirm it sends/advances the expected flow.
5. Verify both the immediate card state and the final result card, not just the assistant's prose.
6. Check console output after every interaction.

## Pitfalls

- Dynamic chat streams invalidate browser snapshot refs quickly. Avoid batching `browser_type`/`browser_click` against stale refs after a card expands; refresh the snapshot before interacting with the composer again.
- If the accessibility tree is too large or refs are stale, use `browser_console` with a targeted DOM query to click a uniquely identified card button.
- Button text that routes through an LLM should be explicit enough to avoid an extra confirmation loop when the intended action is already confirmed (for example checkout buttons should send a confirmed-submit instruction if that is the expected one-click behavior).
- Do not treat a successful API response as enough for UI criteria. Confirm the actual visible card and its interactive controls in the browser.
