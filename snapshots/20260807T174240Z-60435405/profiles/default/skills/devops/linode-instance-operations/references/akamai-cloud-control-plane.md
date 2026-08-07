# Akamai Cloud control-plane reference map

Check these official sources at execution time; product controls and UI/API/CLI workflows can change. All links below were confirmed reachable (HTTP 200) on 2026-08-07.

| Need | Primary reference |
| --- | --- |
| Platform orientation | [Get started with Akamai Cloud](https://techdocs.akamai.com/cloud-computing/docs/getting-started) |
| Instance creation | [Create a Linode](https://techdocs.akamai.com/cloud-computing/docs/create-a-compute-instance) |
| **Primary hardening runbook** (provisioning-time + post-creation checklist) | [Set up and secure a Linode](https://techdocs.akamai.com/cloud-computing/docs/set-up-and-secure-a-compute-instance) — this is the closest official equivalent to a "harden your new server" walkthrough; prefer it over improvising a hardening sequence. It documents that SSH keys are the recommended, password-less authentication path and that setting a root password is optional when keys are used. |
| Account SSH public keys | [Manage SSH keys](https://techdocs.akamai.com/cloud-computing/docs/manage-ssh-keys) |
| Account protection | [Security controls for user accounts](https://techdocs.akamai.com/cloud-computing/docs/security-controls-for-user-accounts) |
| Provider firewall | [Getting started with Cloud Firewalls](https://techdocs.akamai.com/cloud-computing/docs/getting-started-with-cloud-firewalls) |
| Metadata Service / cloud-init user-data | [Overview of the Metadata Service](https://techdocs.akamai.com/cloud-computing/docs/overview-of-the-metadata-service) — review any cloud-init user-data against this document before attaching it to an instance; do not treat a cached or third-party example as current. |
| Backups | [Backup service](https://techdocs.akamai.com/cloud-computing/docs/backup-service) |
| Disk encryption | [Local disk encryption](https://techdocs.akamai.com/cloud-computing/docs/local-disk-encryption) |
| Monitoring (basic) | [Monitor and maintain Linodes](https://techdocs.akamai.com/cloud-computing/docs/monitor-and-maintain-a-compute-instance) — Cloud Manager dashboard graphs (CPU/network/disk I/O), email alerts, Lassie (shutdown watchdog) |
| Monitoring (legacy per-server) | [Longview](https://techdocs.akamai.com/cloud-computing/docs/longview) — still supported; detailed system/service (Apache, NGINX, MySQL) metrics |
| Monitoring (current unified platform) | [Akamai Cloud Pulse](https://techdocs.akamai.com/cloud-computing/docs/akamai-cloud-pulse) — newer metrics/dashboards/alerts platform; some features marked "Limited availability" as of this check, verify GA status before depending on it |
| Audit evidence | [Quick start: Audit logs](https://techdocs.akamai.com/cloud-computing/docs/quick-start-audit-logs) |

## Key-first, passwordless provisioning

- The primary hardening runbook and the instance-creation flow both document that adding an SSH public key at creation time is the recommended authentication path, and that setting a root password becomes **optional** once a key is attached — omitting the password produces a secure, password-less configuration from first boot.
- Treat this as the default recommendation for new instances where the current control plane offers it; verify the option is still present in the Cloud Manager / API flow being used, since UI/CLI details can shift between releases.
- If a workflow still requires a root password (compatibility, break-glass, or organizational policy), handle it as a secret from the moment of creation — see Control-Plane Security in `../SKILL.md`.

## Metadata Service / cloud-init user-data

- Akamai's Metadata Service can accept cloud-init-compatible user-data at creation time; see the Metadata Service overview above for the current directive surface and image compatibility.
- This skill treats user-data as **review-only content**: draft it, review it line-by-line for secrets/hard-coded IPs/unscoped directives, confirm image and Metadata Service compatibility, and only then let the user attach it — this skill does not execute provisioning or installer commands itself.

## Disk Encryption vs. Backups — unresolved compatibility gate

Akamai's own documentation on whether platform-managed Disk Encryption and the managed Backups service can be used on the same instance has not been consistent across all documentation surfaces and points in time seen during upkeep of this skill. **Do not carry forward an absolute claim in either direction from this file.** Before choosing a mechanism:

- Re-check the Disk Encryption and Backup service pages linked above directly, for the specific target account/region/plan, at the time of the decision.
- Treat any single dated statement (including older versions of this reference or third-party write-ups) as provisional, not settled.
- Require a tested, independent recovery-path verification regardless of which mechanism(s) are enabled — "enabled" status is not evidence of recoverability.
- Define RPO/RTO first; let the recovery requirement choose the mechanism, not the reverse.

## Verified operational notes

- Akamai documents Cloud Firewalls as a stateful provider-level firewall that can be used together with local Linux firewall software as an additional, optional layer — Cloud Firewall is the primary control.
- For inbound traffic, Cloud Firewall rules are processed before local firewall rules. Test the combined effective policy rather than assuming the layers are interchangeable.
- Cloud Firewall policy on a NodeBalancer does not by itself protect direct access to backend Linodes; secure the backend instances too.
- Current official guidance for SSH daemon hardening centers on `PermitRootLogin no` + `PasswordAuthentication no`, verified independently before enforcement; it does not recommend moving off the default SSH port as a baseline.
- Account security guidance covers MFA/2FA, recovery controls, named users, and restricted access; do not collapse these into a single shared account.

## Drift rule

Do not embed volatile Cloud Manager click paths, unverified CLI/API commands, or executable scripts in the main skill. When a task requires them, inspect the linked official document and validate the target, permissions, effect, and rollback before mutation.
