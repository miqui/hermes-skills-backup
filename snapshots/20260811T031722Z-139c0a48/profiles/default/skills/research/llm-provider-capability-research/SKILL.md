---
name: llm-provider-capability-research
description: Use when comparing LLM/AI providers (OpenAI, Anthropic, Google Gemini, etc.) on multimodal ingestion, structured output, tool support, pricing, or model selection for an architecture decision, OR when verifying any technical/factual claim in a skill, PR, or doc review against a live third-party platform's first-party documentation. Produces a pending recommendation or review verdict backed by live docs, not stale training knowledge.
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

## Generalizing beyond LLM providers: verifying any platform/skill claim against live docs

The same discipline applies whenever you're checking factual/technical claims made about **any**
third-party platform in a skill, PR, or doc review — not just LLM providers. Cloud provider
defaults, security settings, ordering/precedence behavior, service compatibility, and version
minimums all drift and get mis-cited. Two techniques generalize:

- **Terminal-only page-text extraction** (no browser needed) works well for most doc sites:
  `curl -s <url> -o page.html`, then in Python strip tags with `re.sub('<[^<]+?>', ' ', content)`,
  `html.unescape(...)`, and collapse whitespace. This is faster than the browser-console technique
  below when you don't need JS-rendered content.
- **Don't stop at the first keyword hit.** Doc sites built on ReadMe.io/GitBook/Docusaurus (common
  for cloud platforms like Akamai/Linode, not just LLM vendors) repeat topic keywords dozens of
  times in navigation sidebars and embedded page-config JSON blobs before the actual body prose
  appears. Print surrounding context for each match (`text[i-200:i+400]`) and keep scanning past
  nav-only hits until you find the sentence that actually confirms or contradicts the claim.
- **Match wording/direction precisely, not just topic.** A claim like "provider firewall rules are
  processed before local firewall rules" needs a source sentence stating that specific ordering —
  a page that only says "both can be used together" does not confirm it.
- **When live docs are internally inconsistent or genuinely unsettled**, check whether the artifact
  under review already hedges correctly (says "verify at time of use" instead of asserting false
  certainty) rather than penalizing it for declining to state a number the provider itself doesn't
  reliably state.
- **Report findings as claim → source URL → exact quote**, whether the output is a comparison table
  (as in this skill) or a pass/fail review verdict on someone else's document.

## Pitfall: over-hedged claims that dodge a documented fact

Not every questionable claim in a reviewed artifact is genuinely unverifiable — some are
**incorrectly hedging away from a fact the vendor documents plainly**. These are a distinct
failure mode from "claim contradicts docs" and from "claim correctly notes real
version/vendor variance":

- Example found reviewing a JVM-diagnostics skill draft: it said "do not claim
  `jcmd <pid> GC.heap_dump` automatically forces a full GC — verify against the exact
  build," implying the behavior is build-dependent and unknowable. Oracle's jcmd reference
  (`docs.oracle.com/en/java/javase/<ver>/docs/specs/man/jcmd.html`) states plainly under
  `GC.heap_dump`: **"Impact: High --- depends on the Java heap size and content. Request a
  full GC unless the `-all` option is specified."** That's a stable, documented default —
  hedging on it is itself the bug, not appropriate caution.
- Same doc source also confirms `GC.class_histogram` is documented "Impact: High --- depends
  on Java heap size and content," and that `jstack`/`jinfo`/`jmap` carry Oracle's own
  "experimental and unsupported" label (favor `jcmd` equivalents) — useful anchors when
  reviewing any JVM-tooling skill/doc for similar claims.
- The inverse failure also occurs in the same review pass: an artifact stating a hard
  requirement the upstream project itself does NOT impose. Example: a JVM-perf skill draft
  claimed JMH benchmarks "must live in a dedicated JMH module... built into a self-contained
  shaded jar." The JMH project's own README (`github.com/openjdk/jmh` → `README.md`) says the
  opposite of "must": running from an existing module or IDE "is possible... however setup is
  more complex and results are less reliable" — a strong recommendation, not a mandate. This is
  a fourth bucket alongside the three below: **overclaimed rigidity** — a "must"/"required" the
  primary source frames as merely "recommended." Fix by softening to match the source's own
  modal verb (recommended → keep as guidance; must → check whether the source actually says
  must before keeping it).
- When reviewing, sort each flagged claim into one of three buckets and report which:
  (1) **wrong** — contradicts a documented fact, cite the quote; (2) **correctly hedged** —
  genuinely varies by build/vendor/config and the artifact is right to say "verify live";
  (3) **incorrectly hedged** — a stable documented fact dressed up as uncertain. Bucket (3)
  is easy to miss because the artifact "sounds" appropriately cautious; check the primary
  doc anyway rather than accepting hedged language at face value.

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

## Pitfall: search engines and some doc domains block/404 direct navigation

When verifying a claim, don't default to a search-engine query URL — go straight to the primary
source's own domain and known page structure instead:

- `browser_navigate` to `google.com/search`, `bing.com/search`, and `duckduckgo.com/html` all
  routinely hit bot-detection walls (CAPTCHA "sorry" redirect, Cloudflare challenge iframe, empty
  checkbox-only form) rather than returning results. Retrying the same search URL wastes calls —
  switch straight to the vendor's own docs domain.
- Some canonical doc URLs return transport-level errors when guessed rather than followed from a
  live link — e.g. `openjdk.org/jeps/<n>` and `bugs.openjdk.org/browse/<ISSUE-ID>` both reliably
  threw `net::ERR_HTTP2_PROTOCOL_ERROR` in one review pass regardless of retry. When a specific
  doc URL fails outright (not a 404, a protocol/connection error), stop retrying that exact URL —
  pivot to a different first-party surface for the same fact: e.g. for JDK feature/JEP history,
  Wikipedia's "Java version history" page cross-links every JEP by number and confirmed the
  target fact without needing openjdk.org directly.
- For any vendor's per-command/per-API reference facts (exact flags, options, impact/severity
  labels), prefer the vendor's structured reference page over prose blog posts — e.g. for JDK
  jcmd diagnostic commands, `docs.oracle.com/en/java/javase/<ver>/docs/specs/man/jcmd.html`
  enumerates every command's options and Impact rating directly, and matches the live
  `jcmd <pid> help <command>` output structure, which is more authoritative than a third-party
  blog's paraphrase.

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
