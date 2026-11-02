# Multimodal provider comparison — JPG + text + MP3 classification (2026-08 pass)

Context: HackerRank Orchestrate hackathon needed a model to classify local WhatsApp-style
messages containing text, JPG image posters/screenshots, and MP3 voice notes into a routing
decision (notify/digest/mute) with structured fields (action, message_type, reason, confidence,
evidence_message_ids).

## Findings table

| Provider | Native image+text | Native audio (MP3) in same call | Structured output | Preprocessing needed |
|---|---|---|---|---|
| Anthropic Claude (Messages API) | Yes — image content blocks (base64 / URL / file_id) | No — no audio content type in Messages API | First-party enforced JSON schema (`output_config.format`, `client.messages.parse()`) | Separate ASR pass required for voice notes |
| OpenAI (Responses API) | Yes — vision input | No — transcription is separate model/endpoint (`gpt-transcribe` / Transcription API) | First-party strict JSON schema structured outputs | Separate transcription call required, same split-pipeline shape as Claude |
| Google Gemini (Interactions API) | Yes | Yes — audio inline (<20MB) or via Files API in the *same* request as image+text | `response_schema` constrained JSON in the same call | None — single model call handles all three modalities |

## Recommendation given (explicitly pending user architecture review — not final)

- **Primary: Claude** (e.g. `claude-opus-5` family) for image+text classification with structured
  JSON output, paired with a separate ASR pass for voice notes. Reason given: an Anthropic
  credential was already configured in this environment, so this is the lowest-friction path to
  a working pipeline even though it needs one extra ASR stage.
- **Fallback: Gemini** (e.g. `gemini-3.6-flash`) for true single-model native ingestion of
  JPG+MP3+text in one call. Contingent on provisioning a Gemini API key (not present/displayed in
  this environment at review time).
- OpenAI was not elevated over Claude because it requires the same split vision+ASR pipeline
  shape as Claude, with no offsetting advantage found in this pass.

## Pitfalls hit while researching

- Guessed OpenAI doc URLs (`/guides/models`, `/guides/model-catalog`) 404'd — the working paths
  were `/guides/images-vision`, `/guides/audio`, `/guides/speech-to-text`, discovered via the
  side-nav links in a page that *did* load.
- `browser_console(expression=...)` blocks raw `fetch()` calls as a sensitive primitive; use DOM
  reads (`document.querySelector('article').innerText`) instead to pull full page text past the
  snapshot's truncation.
- Gemini bills audio input/output at a tokens-per-second-of-audio rate (distinct from text token
  pricing) — factor this into cost comparisons, don't assume flat per-token pricing applies
  uniformly across modalities.
