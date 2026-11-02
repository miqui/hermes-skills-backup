# Jev via OpenRouter /api/alpha/decisions — Verified API Contract

Field shapes below were confirmed against live responses (HTTP 200) from OpenRouter's decisions endpoint with model `typesafe/jev-1.13`. Re-verify on first use of a NEW model version — the contract is not versioned publicly.

## Endpoint

- `POST https://openrouter.ai/api/alpha/decisions`
- Headers: `Authorization: Bearer $OPENROUTER_API_KEY`, `Content-Type: application/json`
- Separate from `/v1/chat/completions` — chat SDKs do not work.

## Request shape

```json
{
  "model": "typesafe/jev-1.13",
  "state": { "nested": "json, only fields the questions need" },
  "questions": {
    "<name>": { "type": "noul",   "instructions": "...", "criteria": {"true": {...}, "false": {...}} },
    "<name>": { "type": "choice", "instructions": "...", "criteria": {"option_a": {...}, "option_b": {...}} },
    "<name>": { "type": "score",  "instructions": "...", "criteria": [{"what": "...", "signals": [...]}] }
  }
}
```

- Every question REQUIRES `instructions` (string | record | array). Sending the question text under any other key (e.g. `text`) is an HTTP 400 with path `questions.<name>.instructions`.
- `choice` options go under `criteria` as a RECORD mapping option-name -> description (not `options`).
- `score` criteria is an ARRAY of level objects. `noul` criteria is a record with `true`/`false` keys, each with `what`/`not_for`/`examples`.
- Questions evaluate in parallel and in isolation; mixing all types in one request is supported and cheap.

## Response shape

Top level: `answers` (per question name), `id`, `model`, `provider`, `usage`.

- noul answer: `{"type": "noul", "noul": 0.98}` — ONLY `type` and `noul`. NO `confidence`, NO `probabilities`.
- choice answer: `{"type": "choice", "choice": "delay", "probabilities": {...}, "confidence": 0.72}`
- score answer: `{"type": "score", "score": 2.01, "probabilities": {...}, "confidence": ..., "legend": {...}}`

Consequence: record-level confidence must come from choice or score answers; noul-only pipelines have no confidence signal. Missing noul confidence is expected — never surface it as an error or force review because of it.

## Operational notes

- Pricing (verified via OpenRouter listing): ~$0.042/M input tokens, output free, 32K context, P50 ~0.26s. Single provider, alpha endpoint — fine for demos/experiments, not load-bearing production without a fallback.
- Smoke-test pattern: build one request from a single real data row via the app's own state/question builders, print only the answer KEYS (never values of anything secret-bearing), compare against the contract above.
- For confidence-gated routing: `review` when composite score falls in a pre-threshold uncertainty band OR recorded confidence < threshold; otherwise act on the typed answer.