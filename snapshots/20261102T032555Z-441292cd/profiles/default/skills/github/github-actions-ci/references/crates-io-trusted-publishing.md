# crates.io Trusted Publishing Workflow (validated)

Validated shape from a real repo (`graphql-http-rust`, 2026-09-04): Rust crate
published to crates.io from GitHub Actions using OIDC Trusted Publishing — no
long-lived API token stored anywhere. PR #14 pattern, all pins verified against
upstream.

## Workflow design (`.github/workflows/publish.yml`)

- **Triggers:** `release: types: [published]` + `workflow_dispatch` (manual
  recovery). Never `pull_request` / `pull_request_target` — publish jobs must
  never run PR-controlled code with publishing credentials.
- **Job 1 `validate`** (no special permissions): tag↔version gate —
  `GITHUB_REF_NAME` (via `env:`, never interpolated into `run:`) stripped of
  `v` must equal the crate version from
  `cargo metadata --no-deps | jq`; reject prerelease tags (`*-`); then a full
  `cargo package -p <crate>` (verification build, not `--no-verify`) plus a
  `--list` log line. No artifact upload needed — the listing is visible in the
  job log; skip extra surface.
- **Job 2 `publish`**: `needs: validate`, `environment: crates-io` (GitHub
  Environment — REQUIRED for Trusted Publishing scoping), then:
  1. `rust-lang/crates-io-auth-action@<sha>` exchanges the runner's OIDC token
     for a short-lived crates.io credential (output `token`; input `url` only).
  2. `cargo publish -p <crate>` with `CARGO_REGISTRY_TOKEN: ${{ steps.auth.outputs.token }}`
     passed via `env:`.
- **Workflow-level `permissions: contents: read`; `persist-credentials: false`**
  on every checkout; explicit `timeout-minutes` on both jobs.

## One-time setup (ORDER MATTERS — verified against crates.io/docs/trusted-publishing)

⚠️ Do NOT tell the user Trusted Publishing can be configured before the first
publish. It is a per-crate setting on the crate's own settings page, and only
crate owners can set it — the crate must already exist on crates.io. The first
publish therefore always uses a local API token (`cargo login`), never OIDC.
Wrong click path once given to a user and corrected: there is no
"account → publish graph → Trusted Publishing" page.

1. Publish v0.1.0 locally with the user's API token (rehearse with
   `cargo package` first; publishing burns the version number permanently).
2. GitHub repo → Settings → Environments → create the environment named in the
   publish job (e.g. `crates-io`), optionally with a tag-pattern branch policy
   `v*` or a required reviewer — a free human gate. Recipe:
   `gh api -X PUT repos/<o>/<r>/environments/crates-io` with body
   `{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}`,
   then `gh api -X POST repos/<o>/<r>/environments/crates-io/deployment-branch-policies
   -f name='v*'` (the endpoint is `deployment-branch-policies`, NOT
   `branch-policies` — that 404s).
3. User (crate owner): `crates.io/crates/<name>/settings` → Trusted Publishing
   → Add → GitHub: repository owner, repo name, workflow filename
   (`publish.yml`), environment name (must match the job's `environment:`).
4. Optional hardening: enable "Trusted Publishing Only" mode on the crate —
   disables API-token publishing entirely.
5. Release flow thereafter: tag `vX.Y.Z` matching crate version → create
   GitHub Release → both jobs run → crate publishes with zero stored secrets.

Also note: crates.io itself BLOCKS the `pull_request_target` and `workflow_run`
triggers from Trusted Publishing token exchange — a further reason the workflow
must trigger on `release`/`workflow_dispatch` only.

## Verified action pins (as of 2026-09-04 — re-resolve before reuse)

| Action | Version | Commit SHA |
|---|---|---|
| `actions/checkout` | v7 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `dtolnay/rust-toolchain` | stable (branch tip) | `6bed0761d98439e5a578e2877258200ad565ba87` |
| `Swatinem/rust-cache` | v2.9.2 | `6323deb102c322ba6fcbdcafc7e3dddab59af2b6` |
| `rust-lang/crates-io-auth-action` | v1.0.5 | `c6f97d42243bad5fab37ca0427f495c86d5b1a18` |

## SHA-resolution recipe (per security-review skill: verify, don't trust)

- `GET /repos/<o>/<a>/git/refs/tags/<v>` on an **annotated** tag returns the
  tag *object* SHA, not the commit. Dereference with a second call:
  `GET /repos/<o>/<a>/git/tags/<tag-object-sha>` → `object.sha` is the commit.
  (rust-cache v2.9.2 needed this; lightweight tags return the commit directly.)
- `GET /repos/<o>/<a>/releases/latest` is NOT a reliable SHA source: its
  `target_commitish` is the default *branch name* (e.g. `master`), not a SHA.
  Resolve the release's tag ref instead.
- `dtolnay/rust-toolchain` has no version tags — `@stable`/`@master` are branch
  refs. Pinning the branch tip SHA freezes toolchain updates until the pin is
  refreshed (a real tradeoff vs Dependabot's `github-actions` ecosystem, which
  won't update SHA pins by itself). Note the tradeoff in the workflow comment.
- Existing repo conventions may pin by mutable tag (`@v7`, `@v2`). For a NEW
  workflow use full SHAs; don't mass-refactor existing workflows in the same PR.

## Host approval-gate note

Piping `curl` into `python3`/interpreters triggers command-approval security
scans (pipe-to-interpreter HIGH). For SHA resolution: `curl -s -o /tmp/f.json`
then parse the file in a separate step.

## Pre-merge verification limit (important)

A brand-new workflow that exists only on a PR branch CANNOT be dispatch-tested:
`gh workflow run publish.yml --ref <branch>` fails with `HTTP 404: workflow
publish.yml not found on the default branch`. GitHub only recognizes workflows
present on the default branch. Pre-merge, verify: YAML parse, `git diff
--check`, secret scan, existing CI green on the PR, pins resolved. State
plainly that the workflow's first real hosted run happens post-merge (the
validate job's tag gate gets exercised on the first release tag). Do not claim
end-to-end verification that didn't happen.
