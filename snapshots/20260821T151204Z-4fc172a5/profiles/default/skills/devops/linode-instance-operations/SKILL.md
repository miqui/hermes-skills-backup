---
name: linode-instance-operations
description: Use when operating or securing Linode compute instances.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [linode, akamai-cloud, vps, linux-hardening, cloud-firewall, backups]
    related_skills: [terraform-infrastructure, ansible, deployment-engineer, secure-agent-skills]
---

# Linode Instance Operations

## Overview

Use this skill for the lifecycle of an Akamai Cloud (Linode) Linux compute instance: account and access posture, instance provisioning, secure bootstrap, network exposure, backups, observability, recovery, and controlled day-two operations.

This is an **operations and safety** skill, not a copy-paste application-stack installer. It must keep provider-specific instructions current by checking Akamai Cloud documentation at execution time. It does not treat a historical walkthrough, a blog article, a StackScript, or a prompt as authority to make infrastructure changes.

Read `references/feross-modernization.md` when work originates from the Feross Linode setup article. Read `references/akamai-cloud-control-plane.md` for the current official documentation map and verification policy.

## When to Use

Use this skill when:

- Creating, rebuilding, resizing, or retiring a Linode compute instance
- Hardening SSH or operating-system access on an existing Linode
- Defining Cloud Firewall, local firewall, VPC, DNS, backup, monitoring, audit-log, or recovery posture
- Reviewing a Linode instance before production use or after a security/reliability incident
- Translating a dated server walkthrough into a current, provider-aware runbook

Do not use this skill for:

- Application-specific Nginx, database, Node.js, Java, or container configuration; load the relevant service skill
- Kubernetes workloads; use the Kubernetes or LKE-specific workflow
- Creating generic IaC modules; load `terraform-infrastructure` or `ansible`
- Performing unreviewed account-wide changes, bulk deletion, or production recovery without explicit scope and approval

## Operating Model

### Separate inspection from mutation

Classify every action before doing it:

| Class | Examples | Rule |
| --- | --- | --- |
| Read-only | List instances, inspect firewall rules, view backup state, test DNS | May proceed when the target account/project is known. |
| Reversible mutation | Add an SSH key, update a tagged firewall rule, enable a backup service | State the target, expected effect, rollback, and verification first. |
| High-impact mutation | Create/rebuild/resize/delete an instance, restore a backup, change public exposure, rotate access | Require explicit user confirmation of the exact target and scope. |

Never assume that the available Akamai account, API token, or SSH configuration is the intended target. Never print credentials, recovery codes, private keys, or token values.

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
- Prefer password-less provisioning: attach the account SSH public key at creation and skip setting a root password unless a documented compatibility or recovery need requires one. Akamai's own setup guidance recommends SSH-key provisioning over passwords. If you skip the root password, confirm the Lish out-of-band console recovery path (which itself requires a root password to use) is reachable via the documented "reset the root password" procedure before you'd need it in an incident — see Incident and Recovery Sequence.
- If boot-time configuration is needed (user creation, package install, config files), provide it through the platform's Metadata service user-data field at creation. It is consumed by cloud-init on first boot and requires cloud-init >=23.3.1 plus an image with Metadata-service support; user data specifically cannot be submitted for non-supporting distros, though the Metadata API itself stays reachable in-instance regardless of image. Do not assume every supported image accepts user data — check the current supported-distributions list first.
- Use meaningful labels and tags for ownership, environment, cost, and recovery discovery.
- Decide deliberately whether disk encryption, VPC/private networking, reserved IPs, and Cloud Firewall attachment are required.

### Provisioning verification

Before continuing past creation, verify:

- Instance identity, region, image, plan, network interfaces, and public/private IP assignment
- Intended tags and owner metadata
- Initial administrator access works with the expected public key
- Provider firewall is attached and has the intended effective policy
- Backups and monitoring are enabled or an explicit documented exception exists

## Secure Bootstrap and SSH Access

1. Create a named administrator account with only the required sudo access; do not use `root` for routine administration.
2. Prefer key-based SSH. Prefer modern key algorithms such as Ed25519 when supported by the client and server; use another algorithm only for a documented compatibility need.
3. Install the public key with correct ownership and permissions.
4. Open a **separate, verified key-authenticated administrator session** before disabling root SSH login or password authentication. Keep the known-good session open until the new policy is tested.
5. Disable remote root SSH login where appropriate. Disable password SSH authentication only after the key path and break-glass process have been verified.
6. Do not change SSH to a nonstandard port as a default hardening step. A nonstandard port may be a deliberate local policy, but it does not replace key authentication, access restriction, patching, or monitoring.
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

Akamai documents Cloud Firewalls as a stateful provider perimeter and Linux firewall software as host-level policy. Both are often appropriate together:

- Use **Cloud Firewalls** to enforce reusable, account-visible perimeter rules and control traffic before it reaches an instance.
- Use **nftables**, UFW, firewalld, or another appropriate local tool when host-specific logic or software integration requires it. Note that NodeBalancers cannot run host firewall software at all — Cloud Firewalls is the only inbound-rule option for a NodeBalancer.
- Keep the two policies documented and test their combined behavior. Rule-processing order differs by direction: for inbound traffic, Cloud Firewall rules are evaluated before local firewall rules; for outbound traffic, local firewall rules are evaluated first. Do not assume either layer alone determines the effective policy, and remember outbound Cloud Firewall rules are not applied to NodeBalancers.
- Treat Fail2Ban as optional integration with a clear purpose, log source, local firewall behavior, alerting, and rollback. It is not a universal baseline control.

## Backups, Recovery, and Resilience

1. Translate business requirements into RPO and RTO before selecting a backup mechanism.
2. Enable the provider backup service where it is appropriate, but do not mistake instance backup for complete application recovery.
3. Verify coverage for application data, database data, configuration, certificates, and secret recovery paths. Do not place recoverable secrets in source control.
4. Define a restore owner, destination behavior, DNS/IP implications, and a tested verification procedure.
5. Perform and record periodic restore tests. “Backup enabled” without a restore test is incomplete evidence.
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
- Review StackScripts and external deployment scripts as executable supply-chain artifacts. Do not run remote bootstrap scripts blindly.
- Keep secrets out of variables files, shell history, terminal output, screenshots, and repositories.
- Separate plan/validation from apply. Production mutations need target confirmation and post-change verification.

## Common Pitfalls

1. **Copying a 2020 walkthrough verbatim.** Preserve the lifecycle ideas, but verify OS, provider controls, commands, and security recommendations against current official docs.
2. **Treating a Cloud Firewall as the only firewall.** Use a consciously designed provider/host layering model and test effective behavior.
3. **Disabling SSH access before testing the replacement path.** Keep a verified second admin session open until the hardened configuration is known to work.
4. **Using a nonstandard SSH port as the primary defense.** It does not replace key authentication, source allowlists, patching, monitoring, or least privilege.
5. **Enabling backups without a restore exercise.** Backup status alone does not prove recoverability.
6. **Opening direct backend access behind a load balancer.** Protect backend instance IPs as well as the front end.
7. **Embedding app-stack installation in a host-lifecycle skill.** Keep provider/host controls separate from service-specific configuration.
8. **Using ambient account authority.** Confirm the intended account and use scoped, attributable access.
9. **Automating destructive operations without a scope gate.** Rebuild, restore, resize, firewall changes, and deletion require explicit target confirmation.

## Verification Checklist

- [ ] Target account, instance, region, environment, owner, and maintenance window are known
- [ ] OS release is currently supported and the patch/reboot plan is documented
- [ ] Account access uses named users, least privilege, and protected MFA/SSO where applicable
- [ ] Tokens and keys are scoped, secret-safe, and have an owner/rotation plan
- [ ] Named administrator key login has been tested independently before restrictive SSH changes
- [ ] Root/password SSH posture is intentional and verified without lockout
- [ ] Cloud Firewall and any host firewall rules implement the documented allowlist
- [ ] Only intended services are publicly reachable; backend access is protected
- [ ] Backups cover the real recovery scope and a restore test has been recorded
- [ ] Monitoring, audit logs, alerts, and response ownership are operational
- [ ] High-impact changes include approval, rollback, and post-change verification evidence
