# Feross article source map

## Source

- Feross Aboukhadijeh, "How To Set Up Your Linode For Maximum Awesomeness" (feross.org/how-to-setup-your-linode/)
- The article self-identifies as originally published 2012 and last updated June 2020.
- This file is a **paraphrase / source map only** — it does not quote or reproduce the article's substantive text, and the article itself is not treated as a technical authority. Consult current official Akamai Cloud documentation for any actual command, setting, or default.

## What the lifecycle idea is still useful for

The article's high-level sequence (provision → establish non-root admin access → harden remote access/exposure → patch/monitor → plan and test recovery) is a reasonable checklist shape. The specific commands, defaults, and product names in the 2012/2020 article are stale and must not be copied.

## Known-stale points (do not carry forward as fact)

| Area | Why it is stale |
| --- | --- |
| OS version references | Superseded by whatever LTS release is currently supported; verify at execution time. |
| SSH key algorithm defaults | Modern guidance favors Ed25519 over older defaults; verify against current docs. |
| Nonstandard SSH port suggestion | Not an official baseline; see this skill's SSH-hardening guidance. |
| Manual root-password bootstrap assumption | Current control plane supports key-first, passwordless provisioning; verify before assuming a password step is required. |
| Universal Fail2Ban recommendation | Treated here as optional, scoped integration, not a default. |
| Bundled application-stack install steps | Out of scope for this operations skill; hand off to service-specific skills. |
| Backup-enablement framing | This skill requires RPO/RTO definition and a tested restore before trusting any backup claim. |

## Design rule

Use a historical article only as a prompt for "what problems does a new host need to solve," never as a frozen command or configuration reference. Verify every provider control, OS support window, service name, and CLI/API behavior against current official documentation before acting.
