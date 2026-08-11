---
name: cloud-instance-operations
description: Use when hardening cloud VMs. Apply safe baseline controls.
---

# Cloud instance operations

Use this skill when designing, provisioning, hardening, or operating a cloud virtual-machine instance. It covers the infrastructure and operating-system baseline, not application deployment.

## Scope and safety boundary

- Start with the intended workload, operating system, network exposure, data classification, recovery objective, and approved administrative identities.
- Do not create, rebuild, resize, firewall, lock down SSH, rotate credentials, or change backup/encryption settings until the user has approved the concrete instance and network scope.
- Keep an out-of-band recovery route available before any remote-access or firewall change. Verify that a named non-root administrator can establish a separate session before disabling root or password-based SSH access.
- Treat the provider control plane, account identity, network perimeter, guest OS, backups, and observability as separate layers. Do not claim that one replaces the others.
- Keep application servers, databases, package-repository setup, and one-off cron recipes out of this skill unless the user explicitly asks to extend scope.

## Workflow

### 1. Establish authoritative inputs

1. Prefer current official provider documentation and supported product behavior over blogs, historical setup guides, and remembered defaults.
2. Use older articles only as a lifecycle/source map. Identify each recommendation that is version-, image-, region-, or product-dependent before adopting it.
3. Record the exact provider control-plane features involved: region, instance type, network interfaces, firewall attachment, encryption state, backup product, monitoring product, and recovery console.

### 2. Design the baseline before making changes

Obtain or propose a reviewable decision matrix:

| Area | Required decision |
| --- | --- |
| Account access | Individual identities, least privilege, MFA/SSO policy, API-token ownership and rotation |
| Initial access | SSH key ownership, passwordless provisioning policy, named break-glass route |
| Network | Inbound allowlist by protocol/source, required outbound restrictions, IPv4/IPv6 scope |
| Guest OS | Supported image/version, patch policy, administrative user, local firewall role |
| Data protection | Encryption requirement, provider-backup eligibility, off-site copy, restore objective |
| Observability | Metrics, logs/audit events, alerts, notification owner, escalation path |
| Recovery | Console access, documented lockout procedure, tested restore method |

Call out decisions that cannot be changed without a rebuild, migration, or service interruption.

### 3. Apply layered access and network controls

- Prefer attached account SSH keys and passwordless provisioning where the provider supports it.
- Use a named, non-root administrative account with narrowly justified privileged access.
- Validate SSH configuration before reload/restart and preserve a second live administrative session during the change.
- Prefer the provider firewall for the primary external, stateful allowlist. Add the guest firewall only when it supplies a distinct defense-in-depth or host-local policy need.
- Default inbound policy should deny unsolicited traffic; explicitly allow only approved protocols and sources. Review IPv6 independently rather than assuming IPv4 rules cover it.
- Treat Fail2Ban and similar controls as supplemental abuse resistance, never as the sole perimeter.
- Never adopt a nonstandard SSH port as a default baseline recommendation for a new instance — treat it strictly as a separately-scoped local policy choice if a team wants it, and say so explicitly rather than leaving it implied.

### 3a. Review-first cloud-init / provider Metadata user-data

When a provider's Metadata Service (or equivalent, e.g. cloud-init) can accept boot-time user-data:

- Treat drafted user-data as a reviewed document, not an execution shortcut — this skill authors and reviews it, it does not run provisioning or installer commands on the user's behalf.
- Review line-by-line for scope: individually justify each directive (users, ssh_authorized_keys, write_files, runcmd, package/update stanzas); do not paste a stock example into production unmodified.
- Never embed a plaintext password, private key, API token, or hard-coded IP address in user-data. If a secret is genuinely required at boot, source it from a documented platform secrets mechanism.
- Confirm the target image and the Metadata/cloud-init service are compatible with the specific directives used, against current official documentation, before it is attached to any instance.

### 4. Resolve data-protection compatibility before enabling it

Do not infer encryption or backup compatibility from a single page.

1. Check the current official documentation for both the encryption feature and the backup feature.
2. If their stated behavior differs, do not select an implementation based on the apparent contradiction.
3. Mark the issue as a deployment blocker. Verify eligibility in the provider control plane/API for the exact region, plan, disk layout, and filesystem; obtain provider support confirmation if it remains ambiguous.
4. Until resolved, require an application-aware, independently encrypted off-site backup and a documented restore test when confidentiality or recovery is material.
5. Record whether provider backups are file- or block-based, their retention, their location/failure domain, exclusions (such as attached volumes or configuration), and database-consistency requirements.

### 5. Verify and hand over

Before considering the baseline complete, demonstrate:

- the expected ports are reachable only from approved sources;
- unapproved inbound paths are denied;
- non-root key-based administration works in a fresh session;
- the recovery console/lockout path is documented and accessible to the correct people;
- patch status and service health are known;
- backup and restore behavior is tested or explicitly recorded as untested with an owner and deadline;
- monitoring, log retention, alerts, and alert ownership are defined.

Use the provider's current documentation rather than embedding brittle vendor UI sequences or version-specific service commands.

## Common pitfalls

- **Copying a legacy tutorial verbatim:** old OS releases, deprecated repositories, port-hiding as a security control, manual email daemons, and legacy firewall persistence tooling age poorly.
- **Locking out administration:** disabling root/password access, changing SSH ports, or narrowing a firewall before a second administrator session and console-recovery route have been verified.
- **Equating encrypted source disks with encrypted or eligible backups:** source-disk encryption, backup eligibility, and backup-at-rest encryption are independent properties and must be verified separately.
- **Using managed backup as the only recovery plan:** provider backup retention, location, consistency, and deletion behavior may not meet the workload's recovery objectives.
- **Treating monitoring labels as guarantees:** verify product availability and alert coverage for the actual account, region, and service tier.

## References

- `references/linode-control-plane.md` — concise Linode/Akamai-specific evidence and the backup/encryption compatibility caution found during source review. Confirmed 2026-08-07: current Akamai docs support key-first passwordless provisioning (root password becomes optional once an SSH key is attached at creation) and a Metadata Service that accepts cloud-init user-data — both are documented in that reference along with the still-unresolved Disk Encryption vs. Backups compatibility question.
