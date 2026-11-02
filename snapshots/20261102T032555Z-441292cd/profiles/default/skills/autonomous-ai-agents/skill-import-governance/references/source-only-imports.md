# Source-Only Inspection of External Skill CLIs

Use this reference when someone proposes an external `npx`/registry/Git-based skill installer but the request is to inspect, not install.

## Decision Rule

Do not equate an installer command with a safe import workflow. First determine whether it offers a genuinely non-mutating inspect/list operation. If it does not, clone the source repository into an isolated temporary review workspace and inspect the selected skill there.

A temporary package download or source clone may still affect caches or temporary storage. Report that fact, but distinguish it from a corpus/runtime-skill installation.

## Inspection Sequence

1. Read the CLI help and identify installation defaults: scope, target agent, copy versus symlink behavior, confirmation flags, and any telemetry option.
2. Run the documented list/inspect mode with the exact source URL and requested skill name. Do not use force/yes flags.
3. Confirm the source repository owner, default branch, license, and exact resolved revision.
4. Enumerate the entire selected skill directory and inspect all linked files.
5. Scan the candidate artifact with the approved secret scanner and semantically review commands, URLs, install steps, and permission metadata.
6. Verify that the managed corpus inventory has not changed.

## `skills` CLI Observation (v1.5.22)

The `skills` CLI supports a `--list` mode for repository discovery and supports Hermes with agent ID `hermes-agent` (not `hermes`). Its add command supports both user/global scope and project scope; callers should specify the intended scope and agent rather than relying on auto-detection. By default, `--copy` is opt-in, so an install may use symlink behavior.

Use this observation only as a starting point: re-check `npx skills --help` and `npx skills add --help` before any future decision because CLI behavior can change.

## Corpus-Safe Outcome

For a managed corpus, prefer:

- source-only clone at a pinned revision;
- normalized, vendored skill files in an isolated PR;
- explicit attribution/provenance and license handling; and
- a new PR for every upstream revision update.

Avoid direct `skills add` installation into a runtime agent directory, live symlinks to upstream content, and default-branch dependencies.
