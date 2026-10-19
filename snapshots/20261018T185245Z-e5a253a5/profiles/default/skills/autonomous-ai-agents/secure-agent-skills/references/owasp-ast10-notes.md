# OWASP Agentic Skills Top 10 Reference Notes

Source reviewed: https://owasp.org/www-project-agentic-skills-top-10/

## Purpose
These notes capture the risk taxonomy used by the `secure-agent-skills` skill so security guidance remains grounded in the OWASP Agentic Skills Top 10 (AST10) project.

## AST10 Summary Table

- **AST01 — Malicious Skills**
  - Core risk: skills intentionally contain harmful instructions or payloads.
  - Mitigations: trusted-source review, registry scanning, manual inspection, deny-by-default approval.

- **AST02 — Supply Chain Compromise**
  - Core risk: a previously trusted publisher, repository, registry, or artifact becomes compromised.
  - Mitigations: provenance tracking, version pinning, immutable references, checksum/signature verification where available.

- **AST03 — Over-Privileged Skills**
  - Core risk: the skill assumes more filesystem, network, credential, repository, or CI authority than necessary.
  - Mitigations: least-privilege manifests and instructions, explicit scope boundaries, remove unnecessary capabilities.

- **AST04 — Insecure Metadata**
  - Core risk: deceptive names, descriptions, tags, examples, or publisher signals misrepresent what the skill does.
  - Mitigations: metadata review, naming consistency, publisher validation, stale-reference cleanup.

- **AST05 — Unsafe Deserialization**
  - Core risk: structured content such as YAML/JSON/config/scripts is loaded or reused with unsafe assumptions.
  - Mitigations: safe parser expectations, sandboxed loading, no blind trust in embedded config/scripts.

- **AST06 — Weak Isolation**
  - Core risk: skills execute in environments with insufficient containment or unrestricted host access.
  - Mitigations: containerization/sandboxing, network restrictions, explicit host-boundary warnings.

- **AST07 — Update Drift**
  - Core risk: skill content or dependencies silently become unsafe over time due to floating updates or lagging review.
  - Mitigations: immutable pinning, hash verification, review of skill diffs and dependency changes.

- **AST08 — Poor Scanning**
  - Core risk: superficial scanners miss risky natural-language behavior, hidden intent, or linked-file payloads.
  - Mitigations: semantic review, behavioral scanning, full-directory inspection, threat-focused checklists.

- **AST09 — No Governance**
  - Core risk: organizations lack inventories, ownership, approval records, and monitoring for installed skills.
  - Mitigations: skill inventories, owners, review cadence, approval/retirement workflow.

- **AST10 — Cross-Platform Reuse**
  - Core risk: malicious or unsafe skills are ported across agent ecosystems with minimal change.
  - Mitigations: full normalization, ecosystem-residue removal, re-validation for the destination platform semantics.

## Practical Translation for Hermes Skills

For Hermes, the most important review surfaces are:
- `SKILL.md`
- linked `references/*`
- linked `templates/*`
- linked `scripts/*`
- all commands, URLs, installers, package names, and update instructions embedded in any of the above

A skill should be treated as a security-relevant automation artifact, not passive documentation.
