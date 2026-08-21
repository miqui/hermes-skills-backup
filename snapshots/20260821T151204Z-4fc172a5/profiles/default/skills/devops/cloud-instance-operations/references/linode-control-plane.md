# Linode/Akamai Cloud control-plane notes

Use these notes when the cloud provider is Linode/Akamai Cloud. Recheck the linked official pages during planning; provider behavior, regions, and product availability can change.

## Source roles

- Feross Aboukhadijeh, [How To Set Up Your Linode For Maximum Awesomeness](https://feross.org/how-to-setup-your-linode/): historical lifecycle/source map only. Do not reproduce its Ubuntu 18.04, RSA-only, alternate-SSH-port, manual service-stack, or legacy firewall-era recommendations as a current baseline.
- Akamai Cloud, [Set up and secure a Linode](https://techdocs.akamai.com/cloud-computing/docs/set-up-and-secure-a-compute-instance): primary setup and SSH hardening reference. It supports passwordless provisioning, a limited administrative user, Ed25519 keys, provider/local firewall choices, and a Lish-based lockout path.
- Akamai Cloud, [Cloud Firewalls](https://techdocs.akamai.com/cloud-computing/docs/getting-started-with-cloud-firewalls): provider firewall reference. Cloud Firewalls are stateful; inbound defaults to Drop and outbound defaults to Accept. A service can belong to only one Cloud Firewall.
- Akamai Cloud, [Security controls for user accounts](https://techdocs.akamai.com/cloud-computing/docs/security-controls-for-user-accounts): account identity, MFA, individual-user, and access-control reference.
- Akamai Cloud, [Backups](https://techdocs.akamai.com/cloud-computing/docs/backup-service): managed file-based backups, retention, recovery limits, and off-site-backup reference.
- Akamai Cloud, [Disk encryption](https://techdocs.akamai.com/cloud-computing/docs/local-disk-encryption): source-disk encryption behavior and rebuild/region considerations.

## Mandatory compatibility check: disk encryption and Backups

The reviewed official pages currently make incompatible-looking claims:

- The Backups page says its file-based service requires mountable, **unencrypted** `ext3` or `ext4` filesystems and is not compatible with full-disk encryption.
- The Disk encryption page says a backup can be taken from an encrypted disk, but that backup is not itself encrypted; data is encrypted again on restore when encryption is enabled.

Do not resolve this discrepancy by inference. Before selecting managed Backups for an encrypted Linode, verify the actual eligibility in Cloud Manager/API for the exact instance, disk layout, filesystem, region, and plan. If the behavior remains unclear, obtain Akamai confirmation. Until then, use an independently encrypted off-site backup with an application-aware restore test for material data.

## Other operational cautions

- Backup restores can change disk UUIDs and do not restore all instance-level settings; attached Volumes are excluded. Managed file snapshots may not be database-consistent, so application/database-aware dumps or backups may still be necessary.
- Outbound SMTP ports may be restricted for some newer accounts. Do not make a local mail daemon a prerequisite for administrative alerting.
- Cloud Pulse metrics/alerts may have availability constraints; verify the account and region before relying on it. Longview remains documented but should not be treated as the automatic modern default.
