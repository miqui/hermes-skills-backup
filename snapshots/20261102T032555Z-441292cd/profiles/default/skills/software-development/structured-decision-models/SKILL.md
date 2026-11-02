---
name: structured-decision-models
description: "Use when integrating Jev decision-model APIs into app code."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ai, api-integration, python, cli, testing]
    related_skills: [python-dev, ai-engineer, checkpointed-project-kickoff]
---

# Structured Decision Models

## Overview

Decision-model APIs (TypeSafe Jev / "System One" family) are not chat models: you POST a `state` plus typed `questions` and get typed answers (yes/no probability, choice, rubric score) with no text generation. Integration work is composition work — deterministic code owns the workflow, the model only answers narrow atomic questions. This skill covers the integration workflow and the verified API contract.

## Workflow

1. **Smoke-test the raw request first.** Before writing any client code, send ONE minimal real request (curl or a throwaway script) with a hand-built payload. Read the actual response fields — do not derive the request/response shape from docs or examples alone. See `references/jev-openrouter-decisions-api.md` for the verified contract.
2. **Decompose into atomic questions.** One judgment per question, each with explicit instructions and criteria, referencing state paths in backticks. Questions over the same state run in parallel in a single request — batch them.
3. **Compose in code.** Weighted sums of the independent answers, thresholds for the primary decision, an uncertainty band that routes to `review` instead of guessing. Put weights in named constants so tuning is a constant edit, not a prompt rewrite.
4. **Gate on confidence where it exists.** Verify per-primitive which answers carry `confidence` against a live response; a missing field is a contract, not an error. Low confidence OR the uncertainty band => review flag, never a guessed decision.
5. **Ship a dry-run provider.** A deterministic fake provider derived from the input data keeps the CLI, the test suite, and CI keyless and network-free. Real calls need the key from the environment only.
6. **Verify end-to-end live before publishing:** lint, unit tests, then a real run against the API and inspect actual output rows (tallies, flags, error columns) — not just exit code 0.

## OpenAI Decisions API (verified against developers.openai.com docs, Oct 2026)

OpenAI ships a competing decision endpoint, useful for cross-model comparison with Jev:

- `POST https://api.openai.com/v1/decisions`, model `gpt-6-luna`, public beta (no waitlist — limited-preview claims on decisions-api.net/org/com are unofficial clone sites, not OpenAI).
- Request: `model` + `input` (string or user messages with `input_text`/`input_image`) + `questions` array; each question needs `type`, `name`, `instructions`, and criteria.
- Types: `predicate` → `{probability}`; `choice` → criteria is an **array** of `{value, description}` (different from Jev's record!); `score` → `levels` array of `{label, description}`, lowest first.
- Score returns a **probability-weighted average of level indices** (can fall between levels) — NOT Jev's normalized 0-1 + legend. A comparison harness must reconcile score semantics via labels, not arithmetic.
- Answers: array of objects echoed by `name`; predicate has no confidence, choice/score carry `confidence` + per-option `probabilities`. A `refusal` answer type exists (per-question decline, other questions still answered).
- Images: inline base64 data URLs only — no hosted URLs, no `file_id`.
- Pricing: input tokens only, $0.10/1M (no output/cache charges; regional + long-context multipliers apply).
- Independent questions batch in one request; dependent decisions need sequential requests.

## Pitfalls

- **Never trust a docs-derived payload shape.** Schema validation errors (HTTP 400 with per-field paths) only surface on a real call, and the API's error message is the authoritative field list — one minimal smoke test exposes a wrong field name in seconds; discovering it after a full build costs a rebuild.
- **Do not treat a missing optional field as a failure.** If a primitive's answers legitimately omit `confidence`, forcing review on every row makes the gate useless; fall back to the primitives that carry it.
- **Keyless CI by design.** Tests and CI must never need an API key: mock the HTTP boundary (assert URL, auth header, payload shape — never hit the network) and keep the fake provider deterministic from the input.
- **Secrets stay in the environment.** Source keys from env vars (or the approved 1Password `op run --env-file` pattern on this host); never print, log, or persist them; delete temp env files after the run.
- **Decisions endpoints are not chat completions.** Chat SDKs will not work; the endpoint is separate and may be alpha/single-provider — do not build load-bearing production paths on it without a fallback or SLA story.
- **Env-var leakage across manual smoke tests.** Exporting env vars in a shell for a manual CLI smoke test (e.g. `set -a; source test.env`) leaks into that terminal session and can make unrelated `pytest` runs in the same session fail against the wrong base URL/creds (e.g. sandbox vs mocked prod). `unset` them (or use a subshell/`env VAR=... cmd`) before running the test suite again.

## Relationship to other skills

- `python-dev` for the CLI/package structure and stdlib-only conventions.
- `checkpointed-project-kickoff` when the user wants gated design before build; for lean demo repos, a README design section suffices (user-approved scope).