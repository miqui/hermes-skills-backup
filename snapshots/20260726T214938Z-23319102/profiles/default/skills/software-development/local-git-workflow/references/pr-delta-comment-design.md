# Designing concise PR-delta comments for a snapshot-backed repository

Use when reviewers need a compact description of skill changes while the
repository deliberately commits complete, independently restorable corpus
snapshots.

## Preserve the artifact contract

Do **not** narrow a snapshot PR to changed files when the repository's
snapshot contract requires a full tree and hash verification enforces exact
manifest/on-disk correspondence. A delta is reviewer metadata layered on top
of the complete snapshot; it must not alter the snapshot generator, manifest
schema, verification contract, or restore behavior.

## Derive the delta from committed manifests

1. Reuse the CI job that detects changed `snapshots/*/MANIFEST.json` paths
   between the pull request base and head. Pass its snapshot-ID output to the
   comment renderer instead of reimplementing change detection.
2. Select a new snapshot's predecessor by sorting the repository's
   timestamp-prefixed snapshot IDs. Do not depend on host state or an extra
   database.
3. Compare per-profile manifest file metadata (`sha256`, size) and map each
   changed file to the deepest ancestor that contains `SKILL.md`.
4. Render only skill roots grouped as **New**, **Modified**, and **Removed**.
   Report files outside any skill root separately rather than silently hiding
   them. Never render skill contents or secret-scanner matches.

## Idempotent comment delivery

Use one stable HTML marker in every comment body. On each run:

1. List PR issue comments using the GitHub REST issue-comments endpoint.
2. **Paginate every 100-comment page** until the marker is found or a short
   final page is reached. A one-page lookup will eventually create duplicates
   on heavily discussed PRs.
3. PATCH the marked comment when found; POST only when it does not exist.
4. Keep the HTTP function injectable so tests assert GET→PATCH and GET→POST
   sequences without making network calls. Include a regression test where
   the marker appears after page 1.

Use a defensive upper bound for pagination and fail clearly if it is exceeded.

## Workflow security and permissions

- With `pull_request`, fork-originated runs receive a read-only token. For the
  smallest safe implementation, comment only on same-repository PRs using
  `github.event.pull_request.head.repo.full_name == github.repository`; fork
  PRs retain validation and skip the comment cleanly.
- Use the least permission matching the API endpoint. The REST
  `/issues/{number}/comments` path uses `issues: write`; scope it to the
  conditional comment job, while normal jobs retain `contents: read`.
- Check out the PR head with `persist-credentials: false`. Pass an explicit
  `GITHUB_TOKEN` environment variable only to the final API-publishing step,
  not broadly across installation/test commands.
- A contributor able to modify same-repository workflow YAML can deliberately
  request/use workflow token context; fully separating that trust boundary is
  a different architecture. If that threat model is required, use a
  base-context workflow that never checks out or executes PR-head code and
  reads only manifest data as untrusted input. Do not casually switch to
  `pull_request_target` while checking out PR-head code.

## Tests and verification

Test at least: skill-level add/modify/remove output, initial snapshot without
predecessor, unknown snapshot IDs, unscoped files, first-page update,
later-page update, and creation when no marker exists. Then run the full suite,
validate workflow YAML, publish through the local Git wrapper, and confirm the
actual Actions run. A feature-only PR will correctly skip the conditional
snapshot-comment job; separately render an existing real snapshot pair locally
to prove the reported skill delta.
