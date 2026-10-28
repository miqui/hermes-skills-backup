# Pinned Artifact Preparation Evidence

Use this reference while preparing an import proposal. Keep records in the proposal/PR, not in chat memory.

## Immutable source capture

```bash
git -c protocol.file.allow=never clone --filter=blob:none --no-checkout <source-url> <temporary-dir>
git -C <temporary-dir> checkout --detach <full-commit-sha>
git -C <temporary-dir> rev-parse HEAD
```

Require the resulting value to equal the requested full commit SHA. Record the selected skill subtree and hash every vendored file before normalization.

## Secret scan

Use Betterleaks directory mode, not a nonexistent generic `scan` subcommand:

```bash
betterleaks dir <selected-skill-directory> --no-banner --redact=100 \
  --report-format=json --report-path=<temporary-redacted-report>.json
```

Keep only aggregate result evidence in the PR (tool, directory scope, byte/file scope when available, and pass/fail). Do not publish findings or values that could be secrets.

## Overlay baseline guard

1. Export or copy the latest committed snapshot into a new disposable Hermes-home overlay.
2. Compare the overlay with that exact committed snapshot before adding the candidate.
3. Add only the new or changed skill root to the overlay.
4. Invoke the repository’s normal snapshot command with `--hermes-home <overlay>` and output into the clean worktree.
5. Use the generated snapshot ID for validation and PR reporting.

## Native wrapper checklist

- Preserve raw upstream `SKILL.md` and linked files under `references/upstream/` unchanged.
- Put corpus-native `SKILL.md` at the skill root.
- Copy the applicable upstream license/copyright notice.
- Add `UPSTREAM.md` with pin, source subtree, author, licensing, review state, constraints, and re-review triggers.
- Do not expose upstream `allowed-tools`; do not force all references into context.
- Explicitly state that package installs, network access, and other mutation examples in vendored material require user authorization before execution.
