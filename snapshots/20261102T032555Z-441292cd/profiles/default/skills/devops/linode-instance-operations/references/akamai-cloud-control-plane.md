# Akamai Cloud control-plane reference map

Check these official sources at execution time; product controls and UI/API/CLI workflows can change.

| Need | Primary reference |
| --- | --- |
| Platform orientation | [Get started with Akamai Cloud](https://techdocs.akamai.com/cloud-computing/docs/getting-started) |
| Instance creation | [Create a Linode](https://techdocs.akamai.com/cloud-computing/docs/create-a-compute-instance) |
| **Primary hardening runbook** (provisioning-time + post-creation checklist) | [Set up and secure a Linode](https://techdocs.akamai.com/cloud-computing/docs/set-up-and-secure-a-compute-instance) — this is the closest official equivalent to a "harden your new server" walkthrough; prefer it over improvising a hardening sequence |
| Account protection | [Security controls for user accounts](https://techdocs.akamai.com/cloud-computing/docs/security-controls-for-user-accounts) |
| Account SSH public keys | [Manage SSH keys](https://techdocs.akamai.com/cloud-computing/docs/manage-ssh-keys) (confirmed live) |
| Provider firewall | [Getting started with Cloud Firewalls](https://techdocs.akamai.com/cloud-computing/docs/getting-started-with-cloud-firewalls) (confirmed live; the older `cloud-firewall` slug previously in this table was not confirmed and may be stale — use this URL) |
| Firewall layering detail | [Comparing Cloud Firewalls to Linux firewall software](https://techdocs.akamai.com/cloud-computing/docs/comparing-cloud-firewalls-to-linux-firewall-software) — states rule-processing order per direction and NodeBalancer limits |
| Backups | [Backup service](https://techdocs.akamai.com/cloud-computing/docs/backup-service) |
| Disk encryption | [Disk encryption](https://techdocs.akamai.com/cloud-computing/docs/local-disk-encryption) — see the Backups-compatibility caveat below before combining with Backups |
| Metadata/user-data (cloud-init) | [Metadata service](https://techdocs.akamai.com/cloud-computing/docs/overview-of-the-metadata-service) — user-data delivered at creation, consumed by cloud-init on first boot |
| Monitoring (basic) | [Monitor and maintain Linodes](https://techdocs.akamai.com/cloud-computing/docs/monitor-and-maintain-a-compute-instance) — Cloud Manager dashboard graphs (CPU/network/disk I/O), email alerts, Lassie (shutdown watchdog) |
| Monitoring (legacy per-server) | [Longview](https://techdocs.akamai.com/cloud-computing/docs/longview) — still supported; detailed system/service (Apache, NGINX, MySQL) metrics |
| Monitoring (current unified platform) | [Akamai Cloud Pulse](https://techdocs.akamai.com/cloud-computing/docs/akamai-cloud-pulse) — newer metrics/dashboards/alerts platform; some features marked "Limited availability" as of this check, verify GA status before depending on it |
| Audit evidence | [Quick start: Audit logs](https://techdocs.akamai.com/cloud-computing/docs/quick-start-audit-logs) |

## Verified 2020-vs-current deltas (confirmed against live docs)

- **Docs host moved**: `linode.com/docs/guides/...` URLs now mostly 403/bot-block or redirect. The live canonical host is `techdocs.akamai.com/cloud-computing/docs/...`. Don't waste retries hammering the old `linode.com/docs` paths — go straight to techdocs.
- **Disk encryption vs Backups is an unresolved documentation inconsistency, not a settled fact** — the Backups page states its file-based service requires a mountable, **unencrypted** ext3/ext4 filesystem and is "not compatible with full disk encryption." The Disk Encryption page separately describes taking a backup *from* an encrypted disk (the backup itself isn't encrypted; data is re-encrypted on restore), which implies compatibility. Do not resolve this by inference or present it to the user as a clean architectural tradeoff — verify actual eligibility in Cloud Manager/API for the exact instance, disk layout, filesystem, and region, and flag it as an open question until confirmed. Until resolved, recommend an independently encrypted off-site backup with a tested restore for material data.
- **2FA prerequisite**: Akamai requires three security questions to be configured *before* 2FA can be enabled (used for account-recovery verification). Sequence this as a prerequisite step, not a parallel option.
- **SSH daemon hardening, current guidance**: `PermitRootLogin no` + `PasswordAuthentication no` + optionally restrict `AddressFamily` to inet/inet6. Current official guide does **not** recommend moving off port 22 — this reinforces the existing skill guidance that a nonstandard port is a local policy choice, not an official baseline.

## Verified operational notes

- Akamai documents Cloud Firewalls as a stateful provider-level firewall that can be used with local Linux firewall software; using both may be appropriate.
- Rule-processing order is direction-dependent: for inbound traffic, Cloud Firewall rules are processed before local firewall rules; for outbound traffic, local firewall rules are processed first. Test the combined effective policy rather than assuming the layers are interchangeable or that one direction's ordering applies to the other.
- NodeBalancers cannot run host firewall software at all — Cloud Firewalls is the only inbound-rule option for a NodeBalancer, and outbound Cloud Firewall rules are not applied to NodeBalancers.
- Cloud Firewall policy on a NodeBalancer does not by itself protect direct access to backend Linodes; secure the backend instances too.
- Account security guidance covers 2FA, recovery controls, named users, and restricted access; do not collapse these into a single shared account.

## Drift rule

Do not embed volatile Cloud Manager click paths or unverified CLI/API commands in the main skill. When a task requires them, inspect the linked official document and validate the target, permissions, effect, and rollback before mutation.
