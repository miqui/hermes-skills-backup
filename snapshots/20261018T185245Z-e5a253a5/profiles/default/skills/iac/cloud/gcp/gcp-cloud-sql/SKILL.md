---
name: gcp-cloud-sql
description: "Use when provisioning or reviewing GCP Cloud SQL (Postgres/MySQL). Private-IP, HA, backup/PITR, CMEK baseline via gcloud and Terraform."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, cloud-sql, postgres, mysql, terraform, security, iac]
    related_skills: [terraform-infrastructure, cloud-architect, terraform-module-library]
---

# GCP Cloud SQL (Postgres / MySQL) Production Baseline

## Overview

A standalone, secure-by-default baseline for Cloud SQL instances: private IP only,
regional HA, no public IP, no authorized networks, IAM database auth, Auth Proxy access,
deletion protection, backups >= 7 days with PITR, read replicas, CMEK, and a pinned
maintenance window. Examples use `gcloud` and the Terraform `google` provider.

Scope: this is the **baseline only**. Application/service access (which workloads connect,
their service accounts, per-app DB users and grants) is layered separately and must not be
bundled into the instance module.

Commands marked `# UNVERIFIED` were not executed against a live project; flag names change
between gcloud releases, so confirm with `gcloud sql instances create --help`.

## When to Use

- Creating or reviewing a Cloud SQL Postgres or MySQL instance for production.
- Auditing an existing instance against the checklist below.
- Do NOT use for AlloyDB, Spanner, or Cloud SQL for SQL Server (different flags).

## Baseline Requirements

| Control | Requirement |
|---|---|
| Network | Private IP only (`ipv4_enabled=false`), via Private Services Access; no public IP |
| Firewall | `authorized_networks` empty; reach DB only from the VPC via VPC firewall rules (the SG equivalent) scoped to client tags/service accounts, DB port 5432/3306 |
| HA | `availability_type = REGIONAL` (primary + standby in two zones of a region that has >= 3 zones). Note: Cloud SQL HA uses exactly two zones; "3-zone" is satisfied by choosing a 3+ zone region and, for reads, placing replicas in the third zone |
| Auth | IAM database authentication enabled; built-in password users only for break-glass |
| Client access | Cloud SQL Auth Proxy (or language connectors) with `--private-ip`; TLS enforced |
| Protection | `deletion_protection` on (Terraform AND instance setting) |
| Backups | Automated, >= 7 retained, PITR on, log retention >= 7 days |
| Replicas | >= 1 read replica for read scaling / DR (cross-region for DR) |
| Encryption | CMEK (`encryption_key_name`), key in the same region as the instance |
| Maintenance | Explicit window in low-traffic hours, `update_track = stable` |

## gcloud (UNVERIFIED against a live project)

```bash
PROJECT=my-proj; REGION=us-central1; NET=projects/$PROJECT/global/networks/prod-vpc

# One-time: Private Services Access range + peering
gcloud compute addresses create google-managed-services-prod \
  --global --purpose=VPC_PEERING --prefix-length=16 --network=prod-vpc
gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com \
  --ranges=google-managed-services-prod --network=prod-vpc

# Instance (Postgres). For MySQL use MYSQL_8_0, --enable-bin-log, and flag cloudsql_iam_authentication=on
gcloud sql instances create prod-pg \
  --database-version=POSTGRES_16 --edition=ENTERPRISE_PLUS --tier=db-perf-optimized-N-4 \
  --region=$REGION --availability-type=REGIONAL \
  --network=$NET --no-assign-ip \
  --ssl-mode=ENCRYPTED_ONLY \
  --database-flags=cloudsql.iam_authentication=on \
  --backup-start-time=03:00 --retained-backups-count=14 \
  --enable-point-in-time-recovery --retained-transaction-log-days=7 \
  --maintenance-window-day=SUN --maintenance-window-hour=4 \
  --maintenance-release-channel=production \
  --deletion-protection \
  --disk-encryption-key=projects/$PROJECT/locations/$REGION/keyRings/sql/cryptoKeys/sql-key

# Read replica (own CMEK key required in the replica's region)
gcloud sql instances create prod-pg-ro1 --master-instance-name=prod-pg \
  --region=$REGION --network=$NET --no-assign-ip \
  --disk-encryption-key=projects/$PROJECT/locations/$REGION/keyRings/sql/cryptoKeys/sql-key

# IAM DB user (Postgres: user = email without .gserviceaccount.com suffix)
gcloud sql users create app-sa@$PROJECT.iam --instance=prod-pg --type=cloud_iam_service_account

# Auth Proxy over private IP with IAM authn
cloud-sql-proxy --private-ip --auto-iam-authn $PROJECT:$REGION:prod-pg --port 5432
```

## Terraform (google provider >= 5.x)

```hcl
terraform {
  required_providers {
    google      = { source = "hashicorp/google", version = ">= 5.40" }
    google-beta = { source = "hashicorp/google-beta", version = ">= 5.40" }
  }
}

variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "network_id" {
  type = string # projects/<p>/global/networks/<n>
}

variable "kms_key_id" {
  type = string # same region as the instance
}

resource "google_compute_global_address" "psa" {
  name          = "google-managed-services-prod"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network_id
}

resource "google_service_networking_connection" "psa" {
  network                 = var.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psa.name]
}

# CMEK: Cloud SQL service agent needs encrypt/decrypt on the key.
resource "google_project_service_identity" "sql" {
  provider = google-beta
  project  = var.project
  service  = "sqladmin.googleapis.com"
}

resource "google_kms_crypto_key_iam_member" "sql" {
  crypto_key_id = var.kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.sql.email}"
}

resource "google_sql_database_instance" "primary" {
  name                = "prod-pg"
  project             = var.project
  region              = var.region
  database_version    = "POSTGRES_16"
  encryption_key_name = var.kms_key_id
  deletion_protection = true # Terraform-side guard

  depends_on = [google_service_networking_connection.psa, google_kms_crypto_key_iam_member.sql]

  settings {
    edition                     = "ENTERPRISE_PLUS"
    tier                        = "db-perf-optimized-N-4"
    availability_type           = "REGIONAL"
    deletion_protection_enabled = true # API-side guard
    disk_autoresize             = true

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
      ssl_mode        = "ENCRYPTED_ONLY"
      # No authorized_networks blocks: nothing is allow-listed.
    }

    database_flags {
      name  = "cloudsql.iam_authentication" # MySQL: cloudsql_iam_authentication
      value = "on"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true # MySQL: binary_log_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 14
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # UTC
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled = true
    }
  }
}

resource "google_sql_database_instance" "replica" {
  name                 = "prod-pg-ro1"
  project              = var.project
  region               = var.region
  database_version     = "POSTGRES_16"
  master_instance_name = google_sql_database_instance.primary.name
  encryption_key_name  = var.kms_key_id # must be a key in the replica's region
  deletion_protection  = true

  settings {
    edition                     = "ENTERPRISE_PLUS"
    tier                        = "db-perf-optimized-N-4"
    availability_type           = "ZONAL"
    deletion_protection_enabled = true
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
      ssl_mode        = "ENCRYPTED_ONLY"
    }
  }
}

# IAM DB user (baseline creates none for apps; app access is layered separately).
# Example only:
# resource "google_sql_user" "app" {
#   instance = google_sql_database_instance.primary.name
#   name     = "app-sa@${var.project}.iam"
#   type     = "CLOUD_IAM_SERVICE_ACCOUNT"
# }

# VPC firewall (SG equivalent): allow DB port only from tagged clients.
resource "google_compute_firewall" "db_clients" {
  name      = "allow-clients-to-cloudsql"
  network   = var.network_id
  direction = "EGRESS"
  allow {
    protocol = "tcp"
    ports    = ["5432", "3307"] # 3307 = Auth Proxy/server-side proxy port used by Cloud SQL
  }
  destination_ranges = ["${google_compute_global_address.psa.address}/${google_compute_global_address.psa.prefix_length}"]
  target_tags        = ["cloudsql-client"]
}
```

Validate with `terraform fmt -check && terraform init -backend=false && terraform validate`.

## Production checklist

- [ ] `ipv4_enabled=false`; instance shows only a PRIVATE address (`gcloud sql instances describe ... --format='value(ipAddresses)'`)
- [ ] `authorized_networks` empty; no `0.0.0.0/0`
- [ ] Private Services Access range sized (/16 recommended) and non-overlapping
- [ ] `availability_type=REGIONAL`; region has >= 3 zones; failover tested (`gcloud sql instances failover`)
- [ ] `ssl_mode=ENCRYPTED_ONLY` (or stricter)
- [ ] IAM DB auth flag on; app users are IAM users; built-in `postgres`/`root` password stored in Secret Manager, break-glass only
- [ ] Clients use Cloud SQL Auth Proxy/connectors (`--private-ip`, `--auto-iam-authn`)
- [ ] Deletion protection on in both Terraform and instance settings
- [ ] Automated backups >= 7 retained; PITR on; log retention >= 7 days; restore drill done in last quarter
- [ ] >= 1 read replica (cross-region for DR); replica CMEK and deletion protection set
- [ ] CMEK key in same region, rotation enabled, service agent granted key role
- [ ] Maintenance window + `update_track=stable` set; deny-maintenance period for freezes
- [ ] Query Insights / Cloud Monitoring alerts (CPU, disk, replication lag)
- [ ] App access (users, grants, SAs) in a separate layer, not in this module

## Pitfalls

- Terraform `deletion_protection` only blocks `terraform destroy`; the `settings.deletion_protection_enabled` blocks API/console deletion. Set both.
- Destroy of the PSA connection fails while instances exist; also deleted instance names are unusable for ~1 week.
- CMEK cannot be added or changed on an existing instance; recreate/migrate. Key must be in the instance's region and the service agent needs the key role first (use `depends_on`).
- Replicas of CMEK primaries need their own key in their region.
- MySQL PITR uses `binary_log_enabled`; Postgres uses `point_in_time_recovery_enabled`. IAM flag names differ (`cloudsql.iam_authentication` vs `cloudsql_iam_authentication`).
- Changing flags or tier on HA instances triggers restarts; plan during the window.
- Postgres IAM usernames drop the `.gserviceaccount.com` suffix; MySQL truncates to 32 chars of the email prefix.
- `require_ssl` is deprecated; use `ssl_mode`.
- Enterprise Plus requires supported tiers and regions; use `ENTERPRISE` with `db-custom-*` tiers otherwise.
- Private IP-only means local dev needs a bastion/IAP tunnel to run the Proxy; never re-enable public IP as a shortcut.
- Replica promotion breaks the replication link; update Terraform state/config afterwards.
- Firewall egress rules in Terraform only matter if the VPC has deny-by-default egress; verify with Connectivity Tests.
