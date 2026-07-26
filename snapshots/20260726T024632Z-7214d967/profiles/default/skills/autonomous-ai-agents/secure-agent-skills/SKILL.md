---
name: secure-agent-skills
description: "Use when creating, importing, reviewing, approving, or maintaining AI agent skills that must follow a security-first workflow grounded in OWASP Agentic Skills Top 10 risks and mitigations."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [security, appsec, agentic-skills, owasp, skill-authoring, skill-review]
    related_skills: [skill-security-review-gates, hermes-agent-skill-authoring, hermes-agent]
---

# Secure Agent Skills

## Overview

This skill is for **secure authoring and review of AI agent skills**. Use it when a skill will be created, imported from another ecosystem, updated, installed, or approved for use in a real environment.

It is grounded in the **OWASP Agentic Skills Top 10 (AST10)** project, which frames skills as the vulnerable behavior layer between the model and the tools. In practical terms: MCP/tooling controls what an agent can access; skill security controls **what the agent is instructed to do, with which permissions, under which assumptions, and with what blast radius**.

For Hermes, this means you should treat every skill as a security-relevant artifact even when the main file is “just markdown.” Risk can live in:
- `SKILL.md` instructions
- linked `references/*.md`
- `templates/*`
- `scripts/*`
- shell commands included in examples
- URLs, curl commands, installers, package names, and update instructions
- cross-skill references that silently pull in additional capability or trust assumptions

This skill complements `hermes-agent-skill-authoring` by adding a **security review layer**: trust boundaries, least privilege, provenance, hostile-import cleanup, verification, and ongoing governance.

## When to Use

Use this skill when:
- Creating a new Hermes skill that touches files, shell commands, credentials, networks, package managers, CI/CD, infra, repositories, or external services
- Importing or adapting a skill from another ecosystem (OpenClaw, Claude Code, Cursor/Codex, VS Code extensions, blog posts, gists, vendor docs)
- Reviewing an existing skill for safe publication or local approval
- Running the technical review portion of a formal approval process together with `skill-security-review-gates`
- Normalizing a manually added skill before trusting it
- Adding scripts, templates, or references to a skill directory
- Updating a skill that contains install steps, remote downloads, or privileged workflows
- Designing a team policy for which skills may be installed or used

Do **not** use this skill as a substitute for:
- General application security review unrelated to skills
- OS hardening or network security work that does not involve agent skills
- Tool/runtime security analysis of Hermes itself unless the task is specifically about skill behavior and packaging

## Mental Model

Treat a skill as a **policy-bearing automation package**, not as passive documentation.

Ask four questions before trusting any skill:
1. **Origin** — Who authored it, where did it come from, and can that provenance be verified?
2. **Power** — What actions could an agent take if it follows this skill literally?
3. **Scope** — What files, secrets, systems, services, or repos could be affected?
4. **Drift** — How will you notice if the skill, its links, or its dependencies become unsafe later?

## OWASP AST10 Risk Map for Skills

Use this table as the baseline threat model.

| AST | Risk | What it means for Hermes-style skills | Primary controls |
| --- | --- | --- | --- |
| AST01 | Malicious Skills | A skill intentionally instructs harmful actions, data theft, sabotage, persistence, or misleading review behavior | Trusted source review, manual read-through, linked-file inspection, deny-by-default approval |
| AST02 | Supply Chain Compromise | A previously safe source, registry, repo, URL, or maintainer is compromised | Provenance checks, immutable references, version pinning, checksum/hash verification where possible |
| AST03 | Over-Privileged Skills | The skill assumes broad filesystem, network, secret, repo, or CI access not required for the task | Least privilege, narrow scope, explicit path/account targeting, remove unnecessary steps |
| AST04 | Insecure Metadata | Deceptive names, descriptions, tags, links, or examples hide true behavior or impersonate trusted publishers | Metadata review, consistency checks, naming clarity, stale-reference cleanup |
| AST05 | Unsafe Deserialization | Structured files, YAML, JSON, scripts, or templates are loaded/used unsafely or copied from ecosystems with dangerous assumptions | Safe parser expectations, no blind execution, no trust in embedded config/scripts without review |
| AST06 | Weak Isolation | Skill instructions assume execution on a broad-trust host with unrestricted network/process/file access | Sandbox/containment guidance, host-boundary warnings, avoid global paths and blanket commands |
| AST07 | Update Drift | Skill content, packages, commands, URLs, or assumptions change over time and silently become unsafe | Pin versions, review diffs, add verification steps, state update expectations explicitly |
| AST08 | Poor Scanning | Security review is superficial and misses natural-language payloads or risky intent hidden in prose/examples | Full-directory review, semantic inspection, linked-file search, threat-focused checklist |
| AST09 | No Governance | Nobody knows which skills exist, who approved them, or whether they are still in use | Ownership, review cadence, inventories, approval notes, retirement path |
| AST10 | Cross-Platform Reuse | Imported skills carry over unsafe assumptions, tool names, or trust models from another agent ecosystem | Full normalization, ecosystem residue removal, re-validate for Hermes semantics |

## Secure Authoring Rules

### 1) Minimize authority
Write skills so they ask for or use the **smallest viable capability set**.

Good:
- Use exact paths rather than sweeping filesystem instructions
- Use repository-local commands rather than host-global mutation
- Prefer read-only inspection before mutation
- Separate review steps from execution steps
- Explicitly warn when a step requires side effects

Avoid:
- “Search the whole system”
- “Install globally” unless truly required
- “Use any available token/credential”
- “Run with sudo” without a narrow, justified reason
- Broad deletion or recursive mutation commands in examples

### 2) Eliminate hidden execution
A secure skill should never smuggle side effects through examples, templates, or references.

Review every:
- shell snippet
- curl | bash style installer
- package install command
- git hook / CI / startup script
- template that writes secrets, tokens, or host-specific paths
- linked reference file that could be mistaken for passive background material

If a command has side effects, label it as such and make prerequisites explicit.

### 3) Keep trust boundaries visible
State clearly when the skill crosses any of these boundaries:
- local files
- network access
- source control
- package manager
- cloud/API account
- secret-bearing environment
- production systems

Do not bury trust assumptions in narrative paragraphs.

### 4) Prefer immutable references
When the skill depends on external artifacts, prefer:
- pinned versions
- commit SHAs
- immutable release artifacts
- explicit package versions
- checksums or signatures when available

Do not rely on moving targets like “latest” or unpinned default branches unless the task explicitly requires it and the risk is called out.

### 5) Make reviewable claims only
Do not write instructions that imply trust without a verification path.

Bad:
- “This script is safe to run.”
- “The publisher is trusted.”
- “The package is official.”

Better:
- “Verify the publisher/repo ownership before use.”
- “Pin the exact release/version before installation.”
- “Inspect linked scripts/templates before approval.”

## Secure Review Workflow

Use this sequence whenever a skill is created, imported, or updated.

### Phase 1: Source and provenance
- Identify the source of the skill content
- Determine whether the content is first-party, user-local, imported, AI-generated, or copied from another registry/ecosystem
- Check whether URLs, package names, repo owners, or scripts can be tied to a legitimate maintainer
- Flag ambiguous provenance as a blocker, not a footnote

### Phase 2: Full artifact review
Inspect the entire skill directory, not only `SKILL.md`:
- `SKILL.md`
- `references/*`
- `templates/*`
- `scripts/*`
- asset or helper files

Specifically search for:
- secrets or tokens
- remote execution patterns
- destructive shell commands
- unsafe install/update steps
- stale ecosystem tool names and wrappers
- instructions that bypass review, tests, or policy
- misleading metadata or descriptions

### Phase 3: Permission and blast-radius review
Ask:
- What can an agent do if it follows this skill literally?
- Which paths, repos, hosts, or services could be changed?
- Could the skill exfiltrate data, publish code, alter CI, or mutate production assets?
- Does the task really require that power?

Then narrow the skill until the answer is proportionate to the actual use case.

### Phase 4: Update and dependency review
Check for drift risk in:
- package manager commands
- versionless installs
- external URLs
- default branches
- cloned repos
- generated scripts
- referenced standards/docs likely to change over time

Add pinning and re-validation steps where feasible.

### Phase 5: Governance and approval
Before considering the skill ready:
- assign an owner
- define who may approve changes
- state whether the skill is local-only or intended for broader reuse
- note any environment-specific assumptions
- define when the skill should be re-reviewed

## Importing Skills from Other Ecosystems

Imported skills deserve a **zero-trust normalization pass**.

When adapting a skill from another agent ecosystem:
1. Normalize the canonical local name and frontmatter
2. Remove incompatible metadata and tool references
3. Re-check every command for Hermes semantics and local policy fit
4. Re-review linked files; imported residue often survives outside the main file
5. Replace broad, ecosystem-specific trust assumptions with explicit Hermes-native guidance
6. Rebuild the verification checklist so it tests the Hermes version, not the source version

Common residue to remove:
- references to foreign registries or package formats that are not used here
- foreign tool APIs or MCP wrappers that do not exist locally
- assumptions about auto-installed dependencies or privileged runtimes
- “official” trust language copied from a different ecosystem
- commands that assume different directory layouts, auth flows, or agent policies

## Writing Safer Skill Content

### Preferred patterns
- “Review linked scripts before running them”
- “Pin the package/release version”
- “Restrict work to the target repo/path”
- “Call out side effects before executing”
- “Verify the resulting artifact/state after mutation”
- “State required credentials explicitly; do not assume ambient secrets”

### Anti-patterns
- “Install the latest tool globally”
- “Use whatever token is available”
- “Run the provided bootstrap script” with no inspection step
- “Disable checks if they fail”
- “Search and replace across the whole machine/repo” when only one target is needed
- “Trust this source/package because the name looks official”

## Review Prompts to Apply While Reading a Skill

Use these questions as a lightweight manual scanner:
- Does the skill attempt to expand its own authority beyond the user’s stated task?
- Are there any hidden or indirect execution paths in templates, scripts, or references?
- Are any remote resources downloaded or executed without pinning and review?
- Could the skill expose or transmit secrets, repository state, or local files?
- Could a misleading name/description cause accidental approval?
- If this content were malicious, where would the payload most likely be hidden?
- If the upstream source were compromised tomorrow, what part of this skill would become dangerous first?

## Common Pitfalls

1. **Reviewing only `SKILL.md`.** Risk often hides in linked scripts, templates, or copied references.
2. **Treating markdown as non-executable.** Instructions in prose can still drive destructive action.
3. **Trusting “official-looking” names.** Impersonation and metadata deception are part of the threat model.
4. **Approving broad permissions for convenience.** Over-privileged skills create unnecessary blast radius.
5. **Leaving `latest` or floating references in place.** Update drift turns once-safe guidance into future risk.
6. **Importing a skill and only fixing formatting.** True normalization requires semantics, trust, and capability review.
7. **Ignoring environment assumptions.** A skill that is acceptable on a sandbox host may be unsafe on a workstation or production-connected machine.
8. **Failing to define ownership.** Skills without owners do not get reviewed, rotated, or retired.
9. **Assuming scanning is enough.** Natural-language instructions can carry malicious intent even if no signature-based scan fires.
10. **Marking a skill “secure” without a verification path.** Security claims must be backed by specific checks.

## Secret Verification Without Disclosure

When the task is to **verify API keys, tokens, or model credentials are present/configured securely**, do not treat verification as permission to reveal the secret.

Use this pattern:
1. Verify the **code path** that consumes the secret (provider wiring, env lookup, workflow injection, runtime config).
2. Verify the **declared source of truth** (README, deployment docs, CI workflow, `.env.example`, secret manager references).
3. Verify the **local presence state** only as `SET` / `UNSET` (or equivalent boolean), never by printing the value.
4. Verify **leak barriers** around the secret:
   - `.gitignore` / `.dockerignore` entries for `.env*`
   - pre-commit or CI secret scanning
   - audit-log/session redaction hooks when the environment records prompts, tool calls, or transcripts
5. Report the result as a matrix of **where the secret is expected** (local dev, CI, deployed runtime) and **whether that path is configured**.

### Secret-safe reporting rules
- Never echo raw secret values back to the user unless they explicitly request disclosure and there is no safer alternative.
- Prefer statements like `ANTHROPIC_API_KEY=SET` over showing any prefix/suffix.
- Avoid commands that dump entire env files or process environments when a targeted presence check will do.
- In repos with transcript or assessment harnesses, assume terminal output may be logged and keep checks minimally revealing.
- If the repo documents a CI-only secret, distinguish clearly between **CI/deploy availability** and **local development availability**.

### Pitfall: accidental disclosure during "verification"
A common failure mode is proving a secret exists by printing it. That is not verification; it is exposure. The correct proof is:
- code reference showing the variable name,
- workflow/docs showing where it should come from,
- local presence check reported as boolean only,
- confirmation that ignore/redaction/scan controls exist.

## CI Secret-Scan Evidence Hygiene

When a CI or backup validator scans skills, snapshots, templates, or reference documents for likely secrets:

- Preserve high-confidence signatures (provider token formats, cloud key IDs, private-key blocks) while treating broad credential-assignment patterns as heuristics.
- Guard broad patterns against obvious code expressions. For example, an assignment such as `accessToken = jwtService.generateToken(...)` is not a literal credential merely because the variable name contains `accessToken`.
- Add a regression test for every false-positive rule refinement and a companion synthetic positive case, so precision improves without silently weakening detection.
- Emit only **path, category, and line number** in CI findings. Never print the matched value, including in test diagnostics, workflow summaries, or annotations.
- Separate two concerns in CI: validate artifacts introduced or changed by the PR as the PR gate; run all-history scans on a scheduled/manual audit. This keeps legacy warning debt reviewable without drowning out the current change.
- Do not broadly allowlist a file, skill, or credential-name family solely to silence noise. Prefer a narrow, explainable pattern refinement with regression coverage.

## Verification Checklist

- [ ] Provenance of the skill content is known and recorded, or lack of provenance is explicitly treated as a risk
- [ ] The whole skill directory was reviewed, not just `SKILL.md`
- [ ] Side-effecting commands are clearly labeled and scoped
- [ ] No unnecessary filesystem, network, credential, repo, CI, or package-manager authority remains
- [ ] External dependencies, package versions, URLs, or repos are pinned where feasible
- [ ] Imported ecosystem residue and stale trust assumptions were removed
- [ ] Metadata (name, description, tags, links) accurately reflects actual behavior
- [ ] The skill includes explicit review/verification steps after mutation or install actions
- [ ] Ownership and re-review expectations are clear
- [ ] The final skill is safe enough for its intended environment, not merely syntactically valid

## One-Shot Recipes

### Recipe: Create a new secure-by-default skill
1. Draft the skill using `hermes-agent-skill-authoring`
2. Apply the AST10 table above as a threat model
3. Remove unnecessary authority and hidden execution paths
4. Add provenance, pinning, side-effect warnings, and verification steps
5. Review the whole skill directory before final approval

### Recipe: Review an imported skill before use
1. Identify source and trust level
2. Normalize the main file and linked files for Hermes semantics
3. Search for stale ecosystem references, scripts, URLs, and broad commands
4. Re-scope permissions and pin dependencies
5. Approve only after the rewritten Hermes version passes the verification checklist

### Recipe: Decide whether a skill is safe to install locally
1. Inspect provenance and owner
2. Review all linked content and commands
3. Evaluate blast radius on the current host and repos
4. Reject or quarantine if provenance is weak, permissions are broad, or drift risk is high
5. Document the approval basis if retained

### Companion usage
- Load `secure-agent-skills` when you need the deep technical security review.
- Load `skill-security-review-gates` when you need the formal approval decision, ownership rules, constraints, or re-review policy.
- For non-trivial team approvals, load both together.
