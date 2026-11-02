---
name: skill-security-review-gates
description: "Use when reviewing, approving, rejecting, or governing AI agent skills with explicit security gates, ownership, and release criteria grounded in OWASP Agentic Skills Top 10 risks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [security, appsec, governance, review, approval, agentic-skills, owasp]
    related_skills: [secure-agent-skills, hermes-agent-skill-authoring, hermes-agent]
---

# Skill Security Review Gates

## Overview

This skill defines a **team-oriented approval workflow** for AI agent skills. Use it when a skill is not merely being authored, but must be **reviewed, approved, rejected, published, installed, or retained under explicit security controls**.

Where `secure-agent-skills` focuses on secure authoring and deep review technique, this skill focuses on **decision gates**: what must be true before a skill is allowed into use, who owns that decision, what evidence is required, and what conditions force rejection or re-review.

For any non-trivial review, load `secure-agent-skills` together with this skill: use `secure-agent-skills` for the technical threat review, artifact inspection, least-privilege analysis, and normalization work; use this skill for the final approval state, gating decision, ownership, constraints, and re-review policy.

It is grounded in the **OWASP Agentic Skills Top 10 (AST10)** model. The goal is not to prove a skill is perfectly safe; the goal is to ensure the organization applies consistent, evidence-backed approval criteria proportional to the skill’s blast radius.

## When to Use

Use this skill when:
- A new skill is proposed for local or team use
- An imported skill needs a formal go/no-go decision
- A skill update changes commands, dependencies, linked files, URLs, scripts, or trust assumptions
- A team wants a repeatable review checklist for skill approval
- A security, platform, or engineering lead needs release criteria for skill publication
- A skill should be classified as approved, approved-with-constraints, quarantined, or rejected
- You need re-review triggers, ownership rules, or inventory policy for skills

Do **not** use this skill when:
- You only need to draft or edit a skill and no formal approval decision is required
- The task is general software security review unrelated to agent skills
- You need deep remediation guidance more than governance; in that case also load `secure-agent-skills`

## Load Together Guidance

For non-trivial approvals, load both skills:
- `secure-agent-skills` for technical review depth: provenance analysis, hidden-execution review, authority minimization, linked-artifact inspection, and imported-skill normalization
- `skill-security-review-gates` for decision structure: approval state, evidence capture, owner assignment, constraints, rejection basis, and re-review triggers

## Approval States

Every reviewed skill should end in one of these states:

### 1) Approved
Use when:
- provenance is acceptable
- blast radius is understood and proportionate
- linked artifacts were reviewed
- update/drift risks are controlled
- owner and re-review expectations are defined

### 2) Approved with Constraints
Use when the skill is acceptable **only under specific limits**, such as:
- local-only use
- sandbox-only execution
- no production credentials
- no network access unless separately approved
- pinned version or exact artifact only
- restricted to a specific repo/path/account/environment

Constraints must be written explicitly. “Use carefully” is not a valid constraint.

### 3) Quarantined
Use when the skill may be useful but cannot be trusted for normal use yet.
Typical reasons:
- provenance is incomplete
- imported residue remains
- scripts/templates have not been reviewed
- linked content may drift
- the owner is unknown
- a risky capability needs redesign before approval

Quarantine means **retain for analysis but do not approve for routine use**.

### 4) Rejected
Use when the skill should not be used in its current form.
Typical reasons:
- deceptive or malicious behavior
- unjustified privileged access
- hidden execution or exfiltration patterns
- unsafe remote-install/update guidance
- unverifiable provenance combined with meaningful blast radius
- refusal to narrow scope after review findings

## Gate Model

A skill must pass all mandatory gates before it can be marked Approved.

### Gate 1: Provenance Gate
Questions:
- Is the source known?
- Is the maintainer/publisher identifiable?
- Are copied or AI-generated sections clearly identified if relevant?
- Are external repos, URLs, packages, or scripts attributable to legitimate sources?

Fail this gate if:
- the skill’s origin is unknown and the capability is non-trivial
- the skill impersonates a trusted source
- the reviewer cannot determine what content was imported or from where

### Gate 2: Artifact Completeness Gate
Questions:
- Was the entire skill directory reviewed?
- Were `SKILL.md`, `references/*`, `templates/*`, and `scripts/*` all inspected?
- Were external links and commands reviewed, not just mentioned?

Fail this gate if:
- only the top-level markdown was reviewed
- linked files were skipped
- review evidence does not match the actual skill contents

### Gate 3: Authority Minimization Gate
Questions:
- Does the skill ask for more filesystem, network, credential, repo, CI, or package-manager power than required?
- Are commands narrowly scoped?
- Are side effects separated from read-only inspection?

Fail this gate if:
- the skill uses broad or ambient authority without justification
- repo-wide or host-wide mutation is used where narrower targeting is possible
- the skill relies on “whatever credentials are available” style behavior

### Gate 4: Hidden Execution Gate
Questions:
- Are there commands, templates, scripts, or linked references that could trigger side effects indirectly?
- Do examples contain remote execution patterns or bootstrap steps?
- Could a reviewer miss meaningful behavior because it is buried in narrative text?

Fail this gate if:
- execution is hidden in examples or linked files
- remote scripts/installers are included without explicit review steps
- significant behavior is obscured by non-obvious placement or wording

### Gate 5: Metadata Integrity Gate
Questions:
- Do the name, description, tags, and references accurately represent behavior?
- Is the skill clearly named and not impersonating a trusted vendor, project, or owner?
- Are trust claims verifiable?

Fail this gate if:
- metadata understates risk or misstates capability
- descriptions create a false sense of safety
- naming or references are deceptive or stale

### Gate 6: Drift and Dependency Gate
Questions:
- Are package versions, URLs, branches, or artifacts pinned where feasible?
- Could a future upstream change silently alter the risk profile?
- Are re-review triggers defined for updates?

Fail this gate if:
- the skill depends on floating versions or moving external targets without justification
- update risk is ignored
- no re-review trigger exists for meaningful changes

### Gate 7: Environment Fit Gate
Questions:
- Is this skill safe enough for the intended environment?
- Does it assume sandbox, workstation, CI, or production context?
- Are constraints explicit when environment sensitivity matters?

Fail this gate if:
- a skill acceptable in a sandbox is approved for broader use without adjustment
- the skill assumes production-connected access without strong justification
- host policy conflicts are unresolved

### Gate 8: Governance Gate
Questions:
- Who owns the skill?
- Who can approve changes?
- When must the skill be reviewed again?
- Is the skill in an inventory or known review set?

Fail this gate if:
- no owner exists
- no reviewer role is clear
- approval is granted without lifecycle responsibility

## OWASP AST10 Mapping for Review Decisions

Use this shorthand when writing findings:

- **AST01 Malicious Skills** → reject or quarantine unless proven benign through full review
- **AST02 Supply Chain Compromise** → constrain or reject if provenance/pinning is weak
- **AST03 Over-Privileged Skills** → require scope reduction before approval
- **AST04 Insecure Metadata** → block approval until metadata is corrected
- **AST05 Unsafe Deserialization** → block approval until parser/loading assumptions are safe and reviewed
- **AST06 Weak Isolation** → require environment constraints or containment before approval
- **AST07 Update Drift** → require pinning and re-review triggers
- **AST08 Poor Scanning** → require full-directory and semantic review evidence
- **AST09 No Governance** → block approval until ownership and cadence exist
- **AST10 Cross-Platform Reuse** → require full normalization before approval

## Required Review Evidence

A reviewer should be able to point to concrete evidence for approval. At minimum, capture:
- skill name and path
- reviewer name/role
- date of review
- approval state
- short rationale
- constraints, if any
- known residual risks
- owner
- next review trigger or cadence

If evidence is missing, the decision is weaker than it appears. Do not rely on memory or informal chat alone.

## Suggested Decision Record Template

```markdown
Skill: <name>
Path: <path>
Reviewer: <name/role>
Date: <YYYY-MM-DD>
Decision: Approved | Approved with Constraints | Quarantined | Rejected

Summary:
- <1-3 bullets>

AST10 Findings:
- AST0X: <finding>
- AST0Y: <finding>

Constraints:
- <constraint or "none">

Residual Risks:
- <risk>

Owner:
- <team/person>

Re-review Trigger:
- <next change, cadence, or event>
```

## Fast Rejection Criteria

Reject immediately if any of these are found and not convincingly remediated:
- intentional data exfiltration or sabotage logic
- deceptive naming or publisher impersonation
- hidden remote execution/bootstrap behavior
- unjustified broad credential or host access
- destructive commands presented as routine or safe defaults
- imported skills with unknown provenance plus meaningful side effects

## Approval with Constraints Examples

Good constraints:
- “Approved only for sandbox hosts with no production credentials present.”
- “Approved only for repo-local use under `/path/to/repo`.”
- “Approved only at pinned version `X.Y.Z` after linked script review.”
- “Approved for read-only inspection tasks; mutation steps remain blocked.”

Weak constraints:
- “Be careful.”
- “Use common sense.”
- “Only trusted people should run this.”

## Re-Review Triggers

Trigger a new review when any of these change:
- linked scripts/templates/references
- external URLs, packages, or installers
- trust assumptions or owner
- permission scope or target environment
- update instructions or version pins
- imported content from another ecosystem
- any finding tied to AST02, AST07, or AST10

## Common Pitfalls

1. **Approving the idea instead of the artifact.** Review the exact files and links, not the claimed purpose.
2. **Letting approval happen without a named owner.** Unowned skills become permanent shadow risk.
3. **Confusing “not obviously malicious” with “approved.”** Skills can be unsafe without being intentionally malicious.
4. **Ignoring environment fit.** A skill may be acceptable in a lab but unsafe on a developer workstation or CI runner.
5. **Using vague constraints.** Constraints must be enforceable and testable.
6. **Skipping re-review after updates.** Approval does not survive meaningful drift automatically.
7. **Treating imported content as already vetted.** Cross-platform reuse is itself a named risk.
8. **Accepting weak provenance because the capability seems useful.** Utility is not evidence.
9. **Allowing broad permissions to avoid friction.** Convenience approval creates long-term security debt.
10. **Failing to document the decision.** Undocumented approvals are hard to audit and easy to over-trust later.

## Verification Checklist

- [ ] A final decision state was assigned: Approved, Approved with Constraints, Quarantined, or Rejected
- [ ] Provenance was evaluated and recorded
- [ ] The entire skill directory and linked artifacts were reviewed
- [ ] Authority/blast radius was evaluated against the intended use case
- [ ] Metadata accurately reflects behavior and trust level
- [ ] Update/drift risk was evaluated and re-review triggers are defined
- [ ] Environment constraints are explicit where needed
- [ ] An owner is defined
- [ ] Review evidence is recorded in a reusable form
- [ ] The approval decision is proportional to the skill’s actual risk, not its claimed purpose

## One-Shot Recipes

### Recipe: Approve a low-risk local skill
1. Review provenance and entire skill directory
2. Confirm narrow scope and no hidden side effects
3. Verify metadata and version pinning expectations
4. Assign owner and re-review trigger
5. Mark Approved or Approved with Constraints

### Recipe: Quarantine an imported skill
1. Record source and trust gaps
2. Review for imported residue and broad authority
3. Identify which gates failed
4. Block routine use pending remediation
5. Mark Quarantined with explicit next steps

### Recipe: Reject a risky skill cleanly
1. Capture the exact failing gates and AST10-aligned findings
2. Record why constraints are insufficient
3. Mark Rejected
4. Preserve the rationale so the same artifact is not re-approved informally later
