# UPSTREAM.md — Provenance & Security Decision Record

## Status

**Proposed snapshot pending corpus PR review.** This is a recovery build of
the `rust-best-practices` skill, produced in an isolated overlay for review
purposes only. Nothing in this record authorizes or performs installation
into the live Hermes corpus, a git commit, a branch, or a pull request.
Those actions remain separate, explicit steps for a human or a subsequent
authorized agent turn.

## Source

- Upstream repository: https://github.com/apollographql/skills
- Pinned commit SHA: `c288eb80629dd2309eed81f23d693f66a452d043`
- Upstream path: `skills/rust-best-practices`
- License: MIT, Copyright (c) 2024 Apollo Graph, Inc.

## What was vendored

- `references/upstream/SKILL.md` — verbatim copy of the upstream entrypoint.
- `references/upstream/chapter_01.md` … `chapter_09.md` — verbatim copies of
  the nine upstream reference chapters.
- `references/upstream/NOTICE.md` — compact provenance notice for the
  vendored tree.
- `LICENSE` — verbatim copy of the upstream repository's root `LICENSE`.

All vendored files are unedited, byte-for-byte copies of the pinned-SHA
source; this was verified with `diff` against the pinned checkout at
`/tmp/apollographql-skills-c288eb80629dd2309eed81f23d693f66a452d043` before
this record was written.

## Normalization applied in the Hermes-native `SKILL.md`

- **Removed the foreign `allowed-tools` metadata field** present in the
  upstream frontmatter (`allowed-tools: Bash(cargo:*) Bash(rustc:*)
  Bash(rustfmt:*) Bash(clippy:*) Read Write Edit Glob Grep`). Hermes'
  own permission/tool-access model governs execution here; a vendored
  third-party allowlist has no standing in this corpus and is not
  reproduced anywhere in the native entrypoint.
- Preserved `metadata.author: apollographql` and `license: MIT` from the
  upstream frontmatter — no local maintainer identity was substituted.
- Added a progressive-disclosure routing table (chapters 1–9) so agents
  load only the relevant chapter(s) instead of the full upstream corpus
  on every invocation.
- Added an explicit command-execution constraint: the vendored chapters
  and vendored `SKILL.md` contain `cargo`/`rustup`/package-manager command
  examples (e.g. `cargo clippy`, `cargo test --release`, `cargo insta`).
  These are illustrative documentation, not sanctioned automation. No
  such command may be executed by an agent following this skill without
  explicit, per-command user authorization. No scripts, templates, or
  network installers were added to this skill to invoke any such command.

## Security scan

- Tool: `betterleaks` (Gitleaks-compatible secret scanner), binary at
  `/opt/homebrew/bin/betterleaks`.
- Target: the final generated skill directory
  `skills/software-development/rust-best-practices` in this overlay.
- Result: **clean** — "no leaks found" (scanned ~105,877 bytes in ~32ms,
  exit code 0). No secrets, credentials, or tokens detected in the vendored
  chapters, notices, license, or native entrypoint.

## Installation status

- **No live installation performed.** This skill exists only under the
  synthetic Hermes home overlay
  `/tmp/hermes-rust-corpus-home-20260810-230627/skills/software-development/rust-best-practices`.
- The user's live corpus at `/Users/miqui/.hermes` was not read from or
  written to as part of this build.
- No git add/commit/push, branch creation, or pull request was performed.
  Promotion into the live corpus (if ever desired) requires a separate,
  explicitly authorized PR-review workflow.

## Explicitly out of scope for this build

- No scripts, templates, or network installers were added.
- No cargo/rustup/package-manager command was executed.
- No modification to the pinned source checkout or the git worktree's
  tracked history (working tree only; nothing staged or committed).
