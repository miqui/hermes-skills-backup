---
name: typesafe-jev-decisions
description: Use when writing code that calls TypeSafe Jev (System One).
version: 1.1.0
license: MIT
metadata:
  hermes:
    tags: [typesafe, jev, system-one, decisions, openrouter]
---

# TypeSafe Jev (System One) decision models

## What Jev is — and is not

Jev is a *decision* model, not a chat model: you send typed questions about a `state` and get typed answers back. It generates no text, so it can never serve as a chat model, agent brain, or Hermes coordinator — it cannot plan, call tools, or write prose. It is also not reachable through OpenAI-compatible chat endpoints; it has its own API. Docs: https://docs.typesafe.ai/introduction

## API path

Preferred: OpenRouter Decisions API — the user's existing `OPENROUTER_API_KEY` works, no separate TypeSafe account:

```
POST https://openrouter.ai/api/alpha/decisions
Authorization: Bearer $OPENROUTER_API_KEY
{"model": "typesafe/jev-1.13", "state": {...}, "questions": {...}}
```

- Source the key from an env var only — never hardcode, log, or persist it. If the key is not in the shell env, check 1Password refs in `~/.hermes/config.yaml` and run via `op run --env-file=<tmpfile> -- <cmd>`, deleting the tmpfile after.
- Escape the variable when curling under `op run` in a one-liner (`-H "Authorization: Bearer \$OPENROUTER_API_KEY"`): the outer shell expands an unescaped `$VAR` to empty BEFORE `op run` injects it, producing a misleading 401 "Missing Authentication header" that looks like a bad key. Feed request bodies via `--data @file` to keep the command line simple.
- When an `op://Vault/Item` ref fails to resolve on a headless host, do not assume the vault is missing: check which identity op is using. An exported `OP_SERVICE_ACCOUNT_TOKEN` overrides interactive accounts, and a service account sees ONLY the vaults assigned to it — run `env -u OP_SERVICE_ACCOUNT_TOKEN op vault list` and `op account list` to compare, then have the owner grant the vault to the service account for durable headless access (an interactive `eval $(op signin)` session does not transfer to other shells).
- Alternative: TypeSafe's own SDK/HTTP API (`/v1/systemone`, `jev-latest`) — requires a TypeSafe account key the user may not have. Default to OpenRouter.

## Request schema (validated against the live API)

Every question object requires exactly: `type` (`noul` | `choice` | `score`), `instructions` (string, record, or array), `criteria`.

- Noul: `criteria` is a record with `true` / `false` entries, each `{what, not_for?, examples?}`.
- Choice: `criteria` is a RECORD mapping option-name -> description. Never send it as an array or under a key named `options`.
- Score: `criteria` is an array of level objects (`{what, signals?}`).
- Score ANSWERS (verified live): the `score` field is a 0-1 NORMALIZED value, NOT the rubric level number, and carries a `legend` dict mapping "0".."4" to the level objects sent in criteria. Do not feed the raw score into rubric math — convert ONLY via legend label-matching: bucket = min(4, floor(score*5)); take that legend level's `what` label; accept it as the priority/category ONLY if it matches your own enum; absent/malformed legend = failed answer, never arithmetic (no score*4+k fallbacks). Criteria may define 4 levels while the legend has 5 buckets — reconcile via labels, not counts. Deterministic dry-run fakes must mirror this normalized+legend shape so tests match the real contract.
- Reference state fields inside question text with backtick dot paths, e.g. `flight.crew_minutes_remaining`.
- Answers live at `response.answers.<name>`: `noul` (0-1), `choice`, `score`, `probabilities`, `confidence`. Parse defensively per question — a missing field should fail that one record, not the whole run.
- Score answers put the normalized value under `score` (plus `legend`), NOT a generic `value` key. Write PER-TYPE parsers for the documented field names and confirm them with one live request before shipping: a fake and a parser that agree on the same wrong key pass CI green and fail on the first live call.

Pitfall: a 400 with zod-style `expected string|record|array, received undefined` at `questions.<name>.instructions` means the question text was sent under a different key (e.g. `text`) — rename to `instructions`. The same error class hits choice questions that name their option map `options` instead of `criteria`. The error message's `path` field names the exact key to fix; follow it, re-send, and confirm a real 200 before trusting the client code.

## Design pattern (per docs.typesafe.ai)

- Code owns the workflow: deterministic checks in code, Jev only where judgment is needed. Avoid agent while-loops.
- To gate an existing agent loop (ReAct or SDK-driven), prefer an ENFORCED gate in code: wrap every tool executor so each call consults Jev BEFORE executing (ALLOW / DENY / ESCALATE on confidence + risk thresholds), rather than exposing Jev as a discretionary tool the model may skip. Log every decision to an audit file, and ship a deterministic fake client so the gate runs keyless in CI.
- Decompose into atomic questions and send them ALL in one request — they evaluate in parallel and in isolation (no context-rot). Compose answers in code with weighted sums; change coefficients in code, not prompts.
- Route on confidence: low confidence -> flag for review / escalate, never guess. Test thresholds against your own data.
- All three primitives usually apply together: noul for atomic boolean signals, choice for action/category routing, score for a severity rubric.
- "Calibrated probabilities" is dataset-dependent — verify calibration on labeled data of your own before trusting thresholds.

## Pitfalls

- Always verify the request shape with one real (or dry-run-mocked) call before building further — the endpoint is alpha, single-provider, and schema errors surface only at request time.
- For tests/CI, write a deterministic fake decision provider so runs are keyless and network-free; keep the real client behind a provider interface.
- Keep Jev out of load-bearing production paths until there is a second endpoint or an SLA; fine for experiments and gates.
- Dry-run fakes need realistic CONTINUOUS confidence spread, not a few discrete values: a fake emitting only {0.85, 0.6, 0.3} against a 0.70 confidence gate produced a 50% review rate that was a pure granularity artifact (verified live). Before blaming composition, trace the review-trigger distribution — if every review reason is just `low_confidence`, suspect the fake's confidence granularity, not the composition rules.