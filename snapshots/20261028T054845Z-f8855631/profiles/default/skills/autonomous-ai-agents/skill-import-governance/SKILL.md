---
name: skill-import-governance
description: Use when importing third-party skills into a corpus.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [skills, imports, provenance, governance, supply-chain, corpus]
    related_skills: [secure-agent-skills, skill-security-review-gates, hermes-agent-skill-authoring]
---

# Skill Import Governance

## Overview

Use this skill when a third-party skill is proposed for a managed Hermes skill corpus. Treat the upstream artifact as source material, not as a runtime dependency: review an exact revision, normalize it for Hermes, and deliver a vendored snapshot through the corpus review workflow.

This complements `secure-agent-skills`: that skill evaluates safety and authority; this one governs how an approved import enters and evolves in a managed corpus.

See `references/source-only-imports.md` for a proven inspection pattern for external skill-install CLIs.

## When to Use

- A user proposes an upstream Git repository, registry package, or skill-install command for the corpus.
- A skill must retain upstream provenance while becoming a Hermes-native corpus artifact.
- A team needs to evaluate whether to vendor content, symlink an upstream checkout, or install it directly.
- An existing imported skill needs an upstream update.

Do not use this skill for a personal, unreviewed local experiment that is intentionally outside the shared corpus.

## Source-Only Intake Workflow

1. **Do not install first.** Treat third-party skill CLIs as installers, not as review tools. Use their documented list/inspect mode if it is demonstrably non-mutating; otherwise clone into an isolated review workspace only.
2. **Pin the source.** Record the repository URL, exact commit SHA, default-branch state at review time, and upstream license. Do not review a moving branch and then import it as though it were immutable.
3. **Inspect the full artifact.** Review `SKILL.md` and every linked or packaged file under `references/`, `templates/`, `scripts/`, and assets. Run the approved secret scan and search for commands, installers, remote execution, credentials, host-wide paths, and ecosystem-specific tool references. Prefer `betterleaks` over `gitleaks` when both are available (`which betterleaks`) unless the user specifies otherwise — see `references/secret-scan-tool-choice.md` for the exact invocation and result-reporting rules.
4. **Make an explicit decision.** Apply the security approval gates: approved, approved with constraints, quarantined, or rejected. Do not let a successful clone stand in for review.
5. **Normalize for Hermes.** Rewrite the main `SKILL.md` into Hermes-native triggers, guidance, verification, and pitfalls. Remove incompatible metadata and foreign agent/tool assumptions. Never represent imported `allowed-tools` or similar metadata as an enforceable Hermes permission boundary unless Hermes actually enforces it.
6. **Vendor a reviewed snapshot.** Copy the normalized, pinned content into the corpus contribution. Do not use a live symlink, a floating default branch, or an upstream checkout as the installed corpus artifact.
7. **Submit through the corpus workflow.** Use the established isolated overlay, pull request, review, validation, and merge process. The PR must identify the source revision, license/attribution handling, files included, normalization changes, security decision, and update/re-review trigger.

## Provenance and Attribution

Keep provenance clear without confusing source authorship and local maintenance:

- Preserve the upstream author exactly in frontmatter when the user requests it.
- State the source URL and pinned SHA in a dedicated provenance section or structured metadata.
- Preserve license and required notices after verifying the upstream license terms.
- State which content was materially rewritten for Hermes and which references were retained.
- Name the local corpus owner/reviewer separately from the upstream author.

Do not invent author, license, provenance, or approval claims that cannot be verified from the source artifact.

Concrete frontmatter shape for a vendored import (author preserved, provenance structured, local version distinct from upstream's own version field):

```yaml
---
name: <local-skill-name>
description: Use when ...
version: 1.0.0             # this rewrite's own revision — not upstream's version field
author: <upstream-author>  # preserved verbatim, e.g. apollographql
license: MIT
metadata:
  hermes:
    tags: [...]
    related_skills: [...]
  source:
    upstream_repo: https://github.com/<org>/<repo>
    upstream_commit: <full pinned SHA>
    upstream_skill_path: skills/<original-name>
    upstream_license: <license + copyright holder>
    upstream_version: "<upstream's own version field, if any — kept only for traceability>"
    vendored_snapshot: true
---
```

This keeps upstream authorship visible in the field reviewers expect (`author`), while the pinned commit/license/path live in structured metadata rather than prose that can drift. When only a subset of upstream files is generic/portable (e.g. Rust-toolchain chapters) and a subset is ecosystem-specific (e.g. GraphQL/router examples), vendor the generic subset verbatim under `references/upstream/` with a small `NOTICE.md` recording repo/SHA/license, and do the Hermes-native rewriting only in the top-level `SKILL.md` — don't silently edit vendored chapter text just because it contains occasional ecosystem-flavored code comments; flag those as "seen, consciously retained" in the PR instead.

## Authority and Drift Controls

- Keep setup, package installation, environment mutation, network access, and production actions explicitly opt-in.
- Prefer repository-local validation commands over host-wide setup changes.
- Pin every imported revision. An upstream update is a new input and requires a new diff and re-review.
- Do not make a vendored corpus skill auto-update itself, pull arbitrary remote content, or depend on ambient credentials.
- If upstream examples require tools unavailable in Hermes, replace them with Hermes-native guidance or remove them; do not leave misleading commands in place.

## Pull Request Evidence

Include these items in the PR description:

- upstream repository, exact commit SHA, and license
- artifact inventory: main file plus all linked/support files
- scan and semantic-review results
- commands/URLs/installers found and how they were constrained or removed
- normalization summary, including any behavior intentionally changed for Hermes
- attribution/provenance placement
- owner and trigger for re-review (at minimum, any upstream revision update)

## Common Pitfalls

1. **Using an installer as the import mechanism.** Third-party CLIs may choose a scope, an agent target, symlink behavior, or telemetry flow that does not match corpus governance.
2. **Pinning after review.** The SHA must be known before content review; otherwise the reviewed artifact is ambiguous.
3. **Copying only `SKILL.md`.** Critical commands and imported residue often live in reference files.
4. **Using a live symlink for convenience.** This bypasses pull-request review when upstream changes and makes the installed corpus non-reproducible.
5. **Preserving foreign permission metadata verbatim.** Metadata from another agent ecosystem can imply controls that Hermes does not enforce.
6. **Losing upstream attribution during normalization.** Preserve verified authorship and license obligations while clearly separating local maintenance.
7. **Treating a passed secret scan as full approval.** Scanning cannot evaluate natural-language instructions, authority, or update drift.

## Verification Checklist

- [ ] Source-only clone or documented non-mutating inspection completed; no corpus runtime install occurred.
- [ ] Repository URL, exact SHA, and license were recorded before review.
- [ ] Entire selected artifact, including support files, was inspected and secret-scanned.
- [ ] External commands, downloads, credentials, and host-impacting steps were reviewed and constrained.
- [ ] Imported content was normalized for Hermes; incompatible metadata and foreign assumptions were removed.
- [ ] Upstream author, provenance, and license requirements were preserved as appropriate.
- [ ] Installed corpus content is a vendored snapshot, not a live symlink or floating branch.
- [ ] The contribution is delivered through the corpus PR/validation workflow with an explicit re-review trigger.
