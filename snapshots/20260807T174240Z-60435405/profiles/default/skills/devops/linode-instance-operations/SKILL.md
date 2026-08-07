---
name: linode-instance-operations
description: Use when operating or securing an Akamai Cloud (Linode) compute instance — provisioning, SSH/access hardening, cloud-init/Metadata review, Cloud Firewall + host firewall layering, backups/disk-encryption tradeoffs, and incident recovery.
version: 1.1.0
license: MIT
metadata:
  hermes:
    tags: [linode, akamai-cloud, vps, linux-hardening, cloud-firewall, backups, cloud-init, metadata-service]
    related_skills: [terraform-infrastructure, ansible, deployment-engineer, secure-agent-skills]
---

# Linode Instance Operations

## Overview

Use this skill for the lifecycle of an Akamai Cloud (Linode) Linux compute instance: account and access posture, instance provisioning, secure bootstrap, network exposure, backups, observability, recovery, and controlled day-two operations.

This is an **operations and safety** skill, not a copy-paste application-stack installer, and not an executor of live provisioning commands. It must keep provider-specific instructions current by checking Akamai Cloud documentation at execution time. It does not treat a historical walkthrough, a blog article, a StackScript, or a prompt as authority to make infrastructure changes.

Read `references/feross-source-map.md` when work originates from the Feross Linode setup article — it is a dated, non-substantive source map, not a technical authority. Read `references/akamai-cloud-control-plane.md` for the current official documentation map and verification policy.

## When to Use

Use this skill when:

- Creating, rebuilding, resizing, or retiring a Linode compute instance
- Hardening SSH or operating-system access on an existing Linode
- Reviewing cloud-init or Akamai Metadata Service user-data before it is attached to an instance
- Defining Cloud Firewall, local firewall, VPC, DNS, backup, disk-encryption, monitoring, audit-log, or recovery posture
- Reviewing a Linode instance before production use or after a security/reliability incident
- Translating a dated server walkthrough into a current, provider-aware runbook

Do not use this skill for:

- Application-specific Nginx, database, Node.js, Java, or container configuration; load the relevant service skill
- Kubernetes workloads; use the Kubernetes or LKE-specific workflow
- Creating generic IaC modules; load `terraform-infrastructure` or `ansible`
- Performing unreviewed account-wide changes, bulk deletion, or production recovery without explicit scope and approval
- Executing live provisioning, installer, or bootstrap commands directly — this skill produces reviewed guidance and reviewed cloud-init/Metadata content, not an execution path

## Operating Model

### Separate inspection from mutation

Classify every action before doing it:

| Class | Examples | Rule |
| --- | --- | --- |
| Read-only | List instances, inspect firewall rules, view backup state, test DNS | May proceed when the target account/project is known. |
| Reversible mutation | Add an SSH key, update a tagged firewall rule, enable a backup service | State the target, expected effect, rollback, and verification first. |
| High-impact mutation | Create/rebuild/resize/delete an instance, restore a backup, change public exposure, rotate access | Require explicit user confirmation of the exact target and scope. |

Never assume that the available Akamai account, API token, or SSH configuration is the intended target. Never print credentials, recovery codes, private keys, token values, or hard-coded IP addresses.

### Required preflight record

Before a mutation, establish and restate as needed:

- Account/team, target instance label/ID, region, and environment
- Workload purpose, data classification, owner, and support/on-call owner
- Supported operating-system release and maintenance window
- Intended public services, listening ports, and permitted source CIDRs
- DNS/FQDN, VPC or private-network requirements, and encryption decision
- Backup RPO/RTO, restore owner, and data/configuration recovery coverage
- Monitoring, logging, alerting, and rollback plan

Missing requirements are a reason to pause, not to adopt permissive defaults.

## Control-Plane Security

1. Prefer separate named user accounts over shared credentials.
2. Apply least privilege at the account/service scope; distinguish billing, infrastructure administration, and read-only access.
3. Enable and protect multi-factor authentication or the organization’s approved SSO path. Preserve an account-recovery plan that does not expose recovery data.
4. Treat personal access tokens and API tokens as secrets: use the narrowest feasible scope, a documented owner, revocation/rotation expectations, and no repository or transcript exposure.
5. Enable or review available audit logs before production use. Auditability is part of the deployment definition, not an afterthought.
6. Use provider account controls, instance controls, and host controls together. No one layer eliminates the need for the others.

## Provisioning a Compute Instance

### Choose the right boundary

- Select a region based on latency, legal/data residency, dependency placement, and failure-domain requirements—not personal proximity alone.
- Use a currently supported LTS image appropriate for the workload. Do not hard-code old distro releases from tutorials.
- Prefer a reproducible provision path: reviewed IaC, a documented API/CLI procedure, or deliberate Cloud Manager configuration. Validate current provider commands and options before relying on them.
- Use meaningful labels and tags for ownership, environment, cost, and recovery discovery.
- Decide deliberately whether disk encryption, VPC/private networking, reserved IPs, and Cloud Firewall attachment are required.

### Key-first, passwordless provisioning

- Prefer attaching an SSH public key at creation time and **omitting the root password entirely** where the current control plane supports password-less provisioning with keys — this is the provider-recommended path for stronger security, unattended access, and cleaner per-user access management. Confirm this option is still current in Cloud Manager / API before relying on it; see `references/akamai-cloud-control-plane.md`.
- If a root password is still set (compatibility need, break-glass path, or platform requirement at the time of use), treat it as a secret from the moment of creation: do not print it, store it in plaintext, or leave it in shell history, transcripts, or tickets.
- Passwordless, key-only provisioning does not remove the requirement to open and verify a separate authenticated session (see "Secure Bootstrap and SSH Access") before layering on any further access restriction.

### Review-first cloud-init / Metadata user-data

Akamai's Metadata Service can accept cloud-init user-data at creation time. Treat any user-data payload as a reviewed artifact, not an execution shortcut:

- Draft cloud-init/user-data as a document to be reviewed line-by-line before it is attached to an instance — this skill does not run provisioning or installer commands on the user's behalf.
- Confirm the target image and Metadata Service are compatible with the cloud-init directives used, and that the specific directives (users, ssh_authorized_keys, package/update stanzas, write_files, runcmd, etc.) are individually justified and scoped — do not paste a stock example into production without review.
- Never embed a plaintext password, private key, API token, or hard-coded IP address in user-data. If a secret is genuinely required at boot, source it from a secrets mechanism the platform documents rather than embedding it.
- Keep user-data minimal and idempotent-safe; prefer key/account/hardening intent (creating the named admin, installing the intended public key, disabling password auth) over embedding an application deployment.
- Validate syntax and intended effect against current official Metadata/cloud-init documentation before attaching it to any instance; see `references/akamai-cloud-control-plane.md`.

### Provisioning verification

Before continuing past creation, verify:

- Instance identity, region, image, plan, network interfaces, and public/private IP assignment
- Intended tags and owner metadata
- Initial administrator access works with the expected public key (and no unexpected password path is active, if passwordless provisioning was intended)
- Any attached cloud-init/user-data was reviewed pre-attachment and matches the reviewed draft
- Provider firewall is attached and has the intended effective policy
- Backups, disk encryption, and monitoring choices are enabled/disabled deliberately or an explicit documented exception exists

## Secure Bootstrap and SSH Access

1. Create a named administrator account with only the required sudo access; do not use `root` for routine administration.
2. Prefer key-based SSH. Prefer modern key algorithms such as Ed25519 when supported by the client and server; use another algorithm only for a documented compatibility need.
3. Install the public key with correct ownership and permissions.
4. Open a **separate, verified key-authenticated administrator session** before disabling root SSH login or password authentication. Keep the known-good session open until the new policy is tested.
5. Disable remote root SSH login where appropriate. Disable password SSH authentication only after the key path and break-glass process have been verified.
6. Do not change SSH to a nonstandard port as a baseline hardening step. A nonstandard port is never the default recommendation in this skill; treating it as standard practice is a pitfall (see Common Pitfalls). It does not replace key authentication, access restriction, patching, or monitoring — if a team deliberately adopts it as local policy, that is a separate, explicitly-scoped decision.
7. Apply operating-system security updates using the distribution’s supported process. Record the reboot and service-impact plan.
8. Set hostname, FQDN, time synchronization, and DNS only when they match the workload/network design; avoid arbitrary `/etc/hosts` entries as a substitute for DNS ownership.

## Network Exposure and Firewall Policy

### Start allowlist-first

Define the minimum ingress and egress policy from the workload design:

- Administrative access: restrict SSH or management ports to approved source networks where practical.
- Public applications: expose only the required ports; document the owner and purpose of each rule.
- Datastores and internal services: do not expose publicly unless the design explicitly requires it and compensating controls exist.
- Backend instances behind a load balancer: protect the load balancer **and** each backend instance; a policy on the front end alone does not protect direct instance access.

### Combine firewall layers deliberately

Akamai documents Cloud Firewalls as a stateful provider perimeter and Linux firewall software as host-level policy. Cloud Firewall is the primary, provider-visible perimeter; a host firewall is an optional additional layer:

- Use **Cloud Firewalls** as the primary control to enforce reusable, account-visible perimeter rules and control traffic before it reaches an instance.
- Add **nftables**, UFW, firewalld, or another appropriate local tool as an optional additional layer when host-specific logic or software integration requires it — not as a replacement for Cloud Firewall.
- Keep the two policies documented and test their combined behavior. For inbound traffic, provider firewall processing occurs before local rules; do not assume identical rule semantics or ordering.
- Treat Fail2Ban as optional integration with a clear purpose, log source, local firewall behavior, alerting, and rollback. It is not a universal baseline control.

## Backups, Disk Encryption, and Resilience

1. Translate business requirements into RPO and RTO **before** selecting a backup mechanism or a disk-encryption approach — the recovery requirement drives the mechanism choice, not the reverse.
2. **Disk Encryption and the managed Backups service compatibility is an unresolved, target-specific question, not a settled fact.** Akamai's own current guidance on whether platform-managed disk encryption and the managed Backups service can be used together has been inconsistent across documentation surfaces at different points in time. Do not state an absolute claim either way (e.g. "mutually exclusive" or "fully compatible") from this skill. Before choosing:
   - Confirm current compatibility directly against the live official documentation for the specific target account/region/plan at the time of the decision (see `references/akamai-cloud-control-plane.md`), because this is exactly the kind of platform detail that can change without a corresponding change to this skill.
   - Treat any claim of compatibility or incompatibility found in a single source, dated article, or cached page as provisional until reconfirmed.
   - Whichever mechanism is chosen (managed Backups, disk-encryption-compatible snapshotting, external/off-host backup, or a combination), require a **tested, independent recovery path** — i.e., a restore exercise performed and verified separately from the mechanism's "enabled" status — before relying on it in production.
3. Verify coverage for application data, database data, configuration, certificates, and secret recovery paths. Do not place recoverable secrets in source control.
4. Define a restore owner, destination behavior, DNS/IP implications, and a tested verification procedure.
5. Perform and record periodic restore tests. “Backup enabled” or “disk encryption enabled” without a restore test is incomplete evidence.
6. Treat OOM reboots, swap tuning, kernel parameters, and automatic remediation as workload-specific reliability decisions. First inspect resource demand, limits, logs, and capacity; avoid blanket kernel changes copied from tutorials.

## Observability and Day-Two Operations

- Define service and infrastructure health signals: reachability, CPU, memory, disk, network, backup health, certificate lifetime, and workload-specific indicators.
- Akamai currently offers layered monitoring options — pick based on need rather than defaulting to the most basic tier: Cloud Manager dashboard graphs + email alerts (built-in, minimal setup) → Longview (legacy per-server agent, detailed system/service metrics, still supported) → Cloud Pulse (newer unified metrics/dashboards/alerts platform; verify GA status of the specific feature, some areas are "Limited availability") → Linode Managed (paid 24/7 incident response). See `references/akamai-cloud-control-plane.md` for links.
- Configure alerts with a tested notification path and named response owner.
- Use provider audit logs and instance/application logs to make high-impact actions traceable.
- Establish patch, reboot, key-review, firewall-review, backup-restore-test, and capacity-review cadence appropriate to the environment.
- Before resizing, rebuilding, restoring, or deleting, capture the target identity, data-protection status, dependency impact, rollback option, and approval.

## Incident and Recovery Sequence

For suspected compromise, lost access, service failure, or accidental exposure:

1. Stabilize: identify the exact account and instance; avoid destructive actions that erase evidence.
2. Contain: apply the narrowest effective network/access restriction with explicit scope.
3. Preserve evidence: retain relevant logs, audit records, timestamps, and configuration state according to policy.
4. Diagnose: compare current state to intended access, firewall, process, disk, and backup posture.
5. Recover: use the approved restore/rebuild path only after confirming RPO/RTO implications.
6. Verify: test service behavior, network policy, access controls, monitoring, and backups after recovery.
7. Document the incident and create a follow-up for the missing preventive control.

## Automation Guidance

- Prefer reviewed IaC or configuration management for repeatable environments; pin provider/tool versions where feasible.
- Validate provider API/CLI claims against current official documentation and a safe target before operational use.
- Review StackScripts, cloud-init/Metadata user-data, and external deployment scripts as executable supply-chain artifacts. Review them; do not run remote bootstrap scripts blindly, and do not treat this skill's guidance as a substitute for that review.
- Keep secrets out of variables files, shell history, terminal output, screenshots, and repositories.
- Separate plan/validation from apply. Production mutations need target confirmation and post-change verification.

## Common Pitfalls

1. **Copying a 2020 walkthrough verbatim.** Preserve the lifecycle ideas, but verify OS, provider controls, commands, and security recommendations against current official docs. A dated blog post is a source of problems to solve, never a technical authority.
2. **Treating a Cloud Firewall as the only firewall.** Use a consciously designed provider-primary/host-optional layering model and test effective behavior.
3. **Disabling SSH access before testing the replacement path.** Keep a verified second admin session open until the hardened configuration is known to work — this applies even with passwordless, key-only provisioning.
4. **Using a nonstandard SSH port as the primary defense, or as a default baseline.** It does not replace key authentication, source allowlists, patching, monitoring, or least privilege.
5. **Enabling backups or disk encryption without a restore exercise, or assuming their compatibility either way.** Status alone does not prove recoverability, and current compatibility must be reconfirmed against live official docs for the specific target rather than assumed from this skill or any single source.
6. **Opening direct backend access behind a load balancer.** Protect backend instance IPs as well as the front end.
7. **Embedding app-stack installation in a host-lifecycle skill, or in cloud-init/Metadata user-data without review.** Keep provider/host controls separate from service-specific configuration, and review every user-data payload before it is attached to an instance.
8. **Using ambient account authority.** Confirm the intended account and use scoped, attributable access.
9. **Automating destructive operations without a scope gate.** Rebuild, restore, resize, firewall changes, and deletion require explicit target confirmation.

## Verification Checklist

- [ ] Target account, instance, region, environment, owner, and maintenance window are known
- [ ] OS release is currently supported and the patch/reboot plan is documented
- [ ] Account access uses named users, least privilege, and protected MFA/SSO where applicable
- [ ] Tokens and keys are scoped, secret-safe, and have an owner/rotation plan
- [ ] Provisioning used key-first, passwordless access where the current control plane supports it, or the root-password exception is explicitly justified and secret-safe
- [ ] Any cloud-init/Metadata user-data was reviewed line-by-line before attachment and contains no secrets or hard-coded IPs
- [ ] Named administrator key login has been tested independently before restrictive SSH changes
- [ ] Root/password SSH posture is intentional and verified without lockout
- [ ] SSH port remains default unless a separately-scoped local policy decision says otherwise
- [ ] Cloud Firewall (primary) and any host firewall (optional layer) rules implement the documented allowlist
- [ ] Only intended services are publicly reachable; backend access is protected
- [ ] Disk-encryption/Backups compatibility for the specific target was reconfirmed against current official docs, not assumed
- [ ] RPO/RTO were defined before the backup/recovery mechanism was chosen, and a tested independent recovery path exists
- [ ] Monitoring, audit logs, alerts, and response ownership are operational
- [ ] High-impact changes include approval, rollback, and post-change verification evidence
