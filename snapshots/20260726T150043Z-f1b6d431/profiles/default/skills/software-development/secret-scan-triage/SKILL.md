---
name: secret-scan-triage
description: Use when a secret/credential scanner (gitleaks, trufflehog, hsb-snapshot, custom regex scanners, etc.) flags findings and you must decide whether each is a safe documentation/example placeholder or a potentially live secret — especially when deciding whether to grant a "skip the scan" / "--no-secrets-check"-style exception. Also use when asked to review scan output without revealing secret values.
---

# Secret Scan Triage

Classify scanner findings as **placeholder/example**, **potential secret/blocker**, or **uncertain**,
without ever printing, echoing, or reconstructing the actual secret value — and without altering
files or running the underlying scan/restore/deploy commands unless explicitly asked to.

## When to use
- A tool (hsb-snapshot, gitleaks, trufflehog, git-secrets, custom regex, CI secret-scan step) aborts
  or flags findings and the user needs to decide whether a bypass flag is safe.
- Reviewing a PR/commit that a bot flagged for possible credentials.
- Any request to "check if these are real secrets" or "is it safe to skip the secrets check".

## Method
1. **Get the finding list** (paths + category tags) from the scanner's own output — do not re-run the
   scan yourself unless asked; read the existing report/log.
2. **For each finding, inspect the flagged file with `search_files` scoped to the specific path and a
   narrow pattern** (the credential-shaped keyword: `api_key`, `token`, `password`, `secret`, `AKIA`,
   `ghp_`, `sk-`, `BEGIN ... PRIVATE KEY`, etc.) with a few lines of context. Do not `read_file` the
   whole file if you can avoid it, and never quote a value that looks like it could be a real live
   secret back to the user.
3. **Classification heuristics** (any one is usually sufficient to call it a placeholder):
   - Angle-bracket / `<...>` template values, `YOUR_*`, `your-api-key`, `your-key`, obviously-synthetic
     test fixtures (`"abc"`, `"x"`, `StrongPass1`).
   - Value is read from an env var / CLI flag / secrets manager at runtime — no literal secret in
     source (`os.getenv("X_API_KEY")`, `process.env.KEY`).
   - The doc/file already contains a pre-redaction marker like `«redacted:sk-…»`, `«redacted:ghp_…»`,
     `«redacted:AKIA…»` — this means the source itself has already been through a redaction pass and
     the literal was scrubbed before being committed.
   - Explicit "DO NOT commit real credentials" banner / anti-pattern teaching example (`// DON'T`)
     illustrating what a bad hardcoded secret looks like, often using well-known public sample values
     (e.g. AWS's own canonical demo access key).
   - Fully commented-out YAML/config templates.
   - Test files that skip themselves when a real credential env var is absent.
4. **Call it "potential secret/blocker"** only when you see what looks like a live, unredacted,
   plausible-format literal assigned directly in a non-template, non-test context (no env var read, no
   angle brackets, no "DON'T" framing, no prior redaction marker) — especially in a config file that
   would actually be loaded at runtime.
5. **Call it "uncertain"** when the file is binary/opaque, the surrounding context is insufficient, or
   the value's format is ambiguous — recommend manual owner review rather than guessing.
6. **Report format**: path + category + one-line reason + classification. Do not paste the flagged
   substring itself if it resembles a real secret shape — describe it ("looks like a demo AWS key",
   "reads from env var") instead.
7. **Recommendation**: only endorse a scan-bypass flag (e.g. `--no-secrets-check`) when *every* finding
   classifies as placeholder/example. Any single "potential secret" or "uncertain" finding should block
   the recommendation until a human confirms it.

## Pitfalls
- Don't run the scan/snapshot/restore/deploy command yourself as part of triage — this is a read-only
  review task unless the user explicitly asks you to execute the exception.
- Don't `read_file` large flagged files in full when a scoped `search_files` grep with context lines
  answers the question — avoids accidentally loading a real secret into your own context/output.
- A file that itself contains a scanner's *own* redaction markers (e.g. `«redacted:...»`) is evidence
  the pipeline already sanitized it — treat that as a strong placeholder signal, not a new leak.
- Don't conflate "this file teaches about not hardcoding secrets" with "this file hardcodes secrets" —
  read the surrounding comment/heading before classifying.
