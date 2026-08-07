---
name: llm-provider-capability-research
description: Use when comparing LLM/AI providers (OpenAI, Anthropic, Google Gemini, etc.) on multimodal ingestion, structured output, tool support, pricing, or model selection for an architecture decision. Produces a pending recommendation backed by live first-party docs, not stale training knowledge.
---

# LLM Provider Capability Research

Use this whenever a task asks "which model/provider should we use for X" — multimodal
classification, structured output pipelines, ASR/OCR needs, agent tool use, pricing/latency
tradeoffs. Model capabilities change fast (new model families ship monthly); always verify
against **current first-party docs**, never rely on memorized model names/capabilities.

## Core doc entry points (verify these are still live before trusting a cached URL)

- **Anthropic Claude**: `platform.claude.com/docs/en/build-with-claude/vision` (image ingestion),
  `.../structured-outputs` (JSON schema via `output_config.format` / `client.messages.parse()`).
  As of this review, Claude's Messages API has **no native audio content-block type** — voice/audio
  input requires a separate ASR step before the message reaches Claude.
- **OpenAI**: `developers.openai.com/api/docs/guides/images-vision` (vision input via Responses API),
  `.../guides/structured-outputs` (strict JSON schema), `.../guides/audio` and
  `.../guides/speech-to-text` (transcription is a **separate model/endpoint**, e.g. `gpt-transcribe`,
  not unified with vision in one call).
- **Google Gemini**: `ai.google.dev/gemini-api/docs/audio` (Interactions API — image + audio + text
  can go in **one call**, audio via inline base64 <20MB or Files API upload for larger/reusable files),
  `ai.google.dev/gemini-api/docs/structured-output` (`response_schema` constrained JSON),
  `ai.google.dev/gemini-api/docs/pricing` and `.../docs/models` for current model names/pricing tiers.
  Gemini is the only one of the three (as of this review) that natively ingests image+audio+text
  together in a single request, avoiding separate ASR/OCR preprocessing.

Doc URLs and model names (e.g. `claude-opus-5`, `gemini-3.6-flash`, `gpt-transcribe`) drift over
time — re-verify via the site's own side-nav/model-catalog page rather than assuming a remembered
slug still resolves. Several guessed OpenAI doc paths (e.g. `/guides/models`, `/guides/model-catalog`)
404'd during this review; when a doc URL 404s, use the site's nav sidebar links surfaced in the
snapshot of a page that *did* load, rather than guessing more slugs.

## Comparison framework

For a multimodal/model-selection task, structure the comparison across:
1. **Native multimodal ingestion** — can the one model/API call accept all required media types
   (image, audio, text, video, PDF) in a single request, or does a modality require a separate
   model/endpoint (e.g. dedicated ASR, dedicated OCR)?
2. **Structured output reliability** — is there a first-party enforced JSON-schema / strict-mode
   feature, or only prompt-based "please return JSON" with no guarantee?
3. **Availability / cost / latency** — check the live pricing page, not memory; note free vs paid
   tiers and per-minute/per-token audio billing quirks (e.g. Gemini bills audio input at a
   tokens-per-second-of-audio rate distinct from text tokens).
4. **Preprocessing burden** — if native ingestion is missing for a modality, name the exact
   separate step required (ASR model, OCR pass) and that it adds a pipeline stage, latency, and
   an extra point of failure/cost.

## Working technique: extracting full page text when the snapshot truncates

`browser_navigate`/`browser_snapshot` output on long docs pages truncates (e.g. "[... N more lines
truncated]"). Rather than re-fetching repeatedly, use:
```
browser_console(expression="document.querySelector('article').innerText.slice(START, END)")
```
This pulls the full rendered text of the main content in slices, sidestepping the snapshot's
element-tree truncation and getting past nav-sidebar noise that dominates the compact snapshot.
Note: `browser_console` blocks `expression`s that look like network requests (e.g. raw `fetch()`
calls) as a "sensitive browser JavaScript primitive" — stick to DOM reads (`innerText`,
`textContent`, `querySelector`) which are allowed.

## Output framing

When the ask is "recommend a model," and no user architecture/infra decision has been reviewed yet,
give:
- A **primary candidate** — weight toward what's already provisioned/credentialed in this
  environment if capability differences are otherwise close, and say so explicitly as the reason.
- A **credible fallback** — call out any missing precondition (e.g. "requires provisioning a
  Gemini API key, not currently present") rather than silently assuming availability.
- Label the whole thing explicitly as **pending user architecture review, not a final decision**,
  and do not apply or hard-code the choice into any pipeline/router code without that sign-off.

See `references/multimodal-provider-comparison-2026-08.md` for the specific comparison table and
findings from the most recent pass (Claude vs OpenAI vs Gemini for JPG+text+MP3 classification).
