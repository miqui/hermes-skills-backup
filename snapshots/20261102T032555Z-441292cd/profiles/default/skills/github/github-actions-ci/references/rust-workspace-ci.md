# Rust CI Workflow for GraphQL-Over-HTTP-Style Projects

Validated pattern from a real repo (`graphql-http-rust`, 2026-09-03): Cargo workspace with a core
lib crate + an example binary crate, CI gating every PR, Dependabot for dependency freshness.
All four checks (test ubuntu, test macos, lint, audit) verified SUCCESS on both the initial
push-to-main run and on subsequent PRs.

## CI workflow shape (`.github/workflows/ci.yml`)

- **Triggers:** `pull_request` (all PRs) + `push` to `main`. Every PR gets gated.
- **test job:** matrix over `ubuntu-latest` + `macos-latest`, `cargo test --workspace`.
- **lint job (ubuntu only):** `cargo fmt --all --check` + `cargo clippy --workspace --all-targets -- -D warnings`.
- **audit job:** `cargo install --locked cargo-audit && cargo audit`, `continue-on-error: true`
  (visible but non-blocking — advisories should not hard-block early-stage projects).
- **Toolchain:** `dtolnay/rust-toolchain@stable`; cache with `Swatinem/rust-cache@v2` in every job.
- **Top-level `permissions: contents: read`** — pure read-only gate.

## Mandatory companion: Cargo.lock MUST be committed

`.gitignore` scaffolds often exclude `Cargo.lock`. For a workspace containing ANY binary crate
(an example server, a CLI), commit the lockfile:

1. `cargo audit` **requires** `Cargo.lock` to check — without it the audit job fails or scans nothing.
2. Standard Cargo practice for repos with binaries is to track the lockfile anyway.
3. Fix before publishing: delete the `Cargo.lock` line from `.gitignore`, run `cargo generate-lockfile`, stage it.

Library-only workspaces may keep it ignored, but then the audit job needs a lockfile-generation
step — committing it is simpler.

## Dependabot config (`.github/dependabot.yml`)

```yaml
version: 2
updates:
  - package-ecosystem: cargo
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        update-types:
          - "minor"
          - "patch"
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

Notes:
- `directory: "/"` at a Cargo workspace root covers all members — one cargo entry is enough.
- The `github-actions` ecosystem keeps the actions themselves current (dtolnay, Swatinem, etc.).
- Grouping minor+patch into one PR reduces noise; majors still get dedicated PRs.
- Validate locally with `python3 -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"`
  before committing.

## Publication sequence (git-workflow host)

1. All verification local first: `cargo test --workspace`, `cargo clippy --workspace --all-targets
   -- -D warnings`, `cargo fmt --all --check`, YAML parse check.
2. Betterleaks scan of the working tree (`betterleaks dir . --no-banner`) before the first public push.
3. Initial scaffold: `git init -b main`, stage explicit allowlist, `git-workflow.sh init` (this
   publishes straight to `main` — acceptable only for the empty-repo initial commit; everything
   after goes through `git-workflow.sh change` → PR).
4. Post-publish verification: `gh run list` + `gh run view <id> --json jobs` until all jobs
   report a conclusion; CI success on the push-to-main run is the acceptance evidence.
5. Follow-up changes (badges, dependabot, etc.): fast-forward local `main` from `origin/main`
   first, then `git-workflow.sh change` and verify the PR's check rollup via
   `gh pr view <n> --json statusCheckRollup`.

## Badges that pair with this CI

```markdown
[![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/<repo>/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Rust: stable](https://img.shields.io/badge/rust-stable-orange.svg)
```

If the README shows a License badge, the repo must actually contain a `LICENSE` file —
add it in the same PR (crates declaring `license = "MIT"` in Cargo.toml without a LICENSE file
are a common gap).