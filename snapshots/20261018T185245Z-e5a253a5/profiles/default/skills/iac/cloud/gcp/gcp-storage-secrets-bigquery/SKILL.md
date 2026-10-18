---
name: gcp-storage-secrets-bigquery
description: "Use when hardening GCP Cloud Storage, Secret Manager, or BigQuery. Covers GCS lockdown, secret versions/rotation/IAM, BigQuery IAM, authorized views, cost guards."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, iac, gcs, secret-manager, bigquery, security, terraform, gcloud]
    related_skills: [terraform-infrastructure, cloud-architect]
---

# GCP Storage, Secrets & BigQuery — Hardening

## Overview

Baseline patterns for three data-plane services, with `gcloud`/`bq` and Terraform (`hashicorp/google ~> 6.0`). The Terraform in this skill passed `terraform fmt -check` and `terraform validate` (v1.16.2, `init -backend=false`); no plan/apply was run. Commands marked **(unverified)** were not executed against a real project.

## When to Use

- Creating or auditing buckets, secrets, datasets, or tables.
- Removing secrets from env vars / code; setting rotation.
- Controlling BigQuery spend or sharing a subset of data safely.

## 1. Cloud Storage (GCS)

Checklist: uniform bucket-level access (UBLA), public access prevention (PAP) `enforced`, versioning, retention (if compliance needs it), CMEK, lifecycle rules.

```bash
# (unverified)
gcloud storage buckets create gs://$PROJECT-data --location=US \
  --uniform-bucket-level-access --public-access-prevention \
  --default-encryption-key=$KMS_KEY
gcloud storage buckets update gs://$PROJECT-data --versioning
gcloud storage buckets update gs://$PROJECT-data --retention-period=7d
# IRREVERSIBLE: locks the retention policy
# gcloud storage buckets update gs://$PROJECT-data --lock-retention-period
gcloud storage buckets update gs://$PROJECT-data --lifecycle-file=lifecycle.json
```

```bash
# lifecycle.json (unverified)
{"rule":[
 {"action":{"type":"SetStorageClass","storageClass":"NEARLINE"},"condition":{"age":30}},
 {"action":{"type":"Delete"},"condition":{"numNewerVersions":5,"isLive":false}}]}
```

Inputs assumed by the snippets below:

```hcl
variable "project_id" { type = string }
variable "kms_key_id" { type = string }
variable "app_sa" { type = string }
variable "analyst_group" { type = string }
```

```hcl
resource "google_storage_bucket" "data" {
  name                        = "${var.project_id}-data"
  project                     = var.project_id
  location                    = "US"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  encryption {
    default_kms_key_name = var.kms_key_id
  }

  versioning {
    enabled = true
  }

  retention_policy {
    retention_period = 604800 # seconds
    is_locked        = false  # true is permanent
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }
}
```

Org-wide: enforce constraints `storage.uniformBucketLevelAccess` and `storage.publicAccessPrevention`.

## 2. Secret Manager

- Store each secret as a resource; apps read a **version** at runtime. Pin a version number for prod; `latest` only where auto-pickup is intended.
- IAM **per secret** (`roles/secretmanager.secretAccessor`) to the workload's service account — not project-wide.
- Rotation: Secret Manager only *publishes* a Pub/Sub notification at `next_rotation_time`; your function must add the new version and disable the old.
- Never put secret values in env vars, Terraform vars/state, images, or CI logs.

```bash
# (unverified)
printf '%s' "$VALUE" | gcloud secrets create db-password --data-file=- --replication-policy=automatic
printf '%s' "$NEW"   | gcloud secrets versions add db-password --data-file=-
gcloud secrets versions disable 1 --secret=db-password
gcloud secrets add-iam-policy-binding db-password \
  --member=serviceAccount:$APP_SA --role=roles/secretmanager.secretAccessor
# Cloud Run: mount instead of env var
gcloud run deploy svc --image=$IMG --set-secrets=/secrets/db=db-password:3
```

```hcl
resource "google_secret_manager_secret" "db" {
  secret_id = "db-password"
  project   = var.project_id

  replication {
    auto {}
  }

  rotation {
    next_rotation_time = "2027-01-01T00:00:00Z"
    rotation_period    = "7776000s"
  }

  topics {
    name = "projects/${var.project_id}/topics/secret-rotation"
  }
}

resource "google_secret_manager_secret_iam_member" "app" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.app_sa}"
}
```

Do not manage `google_secret_manager_secret_version` with a literal value: it lands in state. Add versions out-of-band, or use write-only attributes if your provider version supports them.

## 3. BigQuery

- **Dataset IAM** (`google_bigquery_dataset_iam_member`), not broad project roles. Use `dataViewer` on datasets; `jobUser` at project to run queries.
- **Authorized views**: put raw tables in a private dataset, the view in a shared dataset, and authorize the view on the private dataset; analysts get access to the shared dataset only.
- **Partition + cluster** and `require_partition_filter` to bound scans.
- **Cost guards**: `maximum_bytes_billed` per query (fails instead of overspending), dry runs, project/user custom quotas.
- **Pricing**: on-demand bills per TiB scanned (good for spiky/low volume); slots/editions reservations give capacity-based billing (good for steady heavy load). Choose per project via reservation assignments.

```bash
# (unverified)
bq query --use_legacy_sql=false --dry_run 'SELECT ...'
bq query --use_legacy_sql=false --maximum_bytes_billed=10000000000 'SELECT ...'  # 10 GB cap
bq mk --table --time_partitioning_field=event_ts --time_partitioning_type=DAY \
  --require_partition_filter --clustering_fields=user_id $PROJECT:private_raw.events schema.json
bq show --format=prettyjson $PROJECT:private_raw   # edit "access", add view entry
bq update --source access.json $PROJECT:private_raw
```

```hcl
resource "google_bigquery_dataset" "private" {
  dataset_id = "private_raw"
  project    = var.project_id
  location   = "US"
}

resource "google_bigquery_dataset" "shared" {
  dataset_id = "shared_views"
  project    = var.project_id
  location   = "US"
}

resource "google_bigquery_table" "events" {
  dataset_id               = google_bigquery_dataset.private.dataset_id
  table_id                 = "events"
  project                  = var.project_id
  deletion_protection      = true
  require_partition_filter = true

  time_partitioning {
    type  = "DAY"
    field = "event_ts"
  }
  clustering = ["user_id"]

  schema = jsonencode([
    { name = "event_ts", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "user_id", type = "STRING", mode = "NULLABLE" }
  ])
}

resource "google_bigquery_table" "events_view" {
  dataset_id          = google_bigquery_dataset.shared.dataset_id
  table_id            = "events_v"
  project             = var.project_id
  deletion_protection = false

  view {
    query          = "SELECT event_ts FROM `${var.project_id}.private_raw.events` WHERE event_ts > TIMESTAMP '2020-01-01'"
    use_legacy_sql = false
  }
}

resource "google_bigquery_dataset_access" "authorized_view" {
  dataset_id = google_bigquery_dataset.private.dataset_id
  project    = var.project_id

  view {
    project_id = var.project_id
    dataset_id = google_bigquery_dataset.shared.dataset_id
    table_id   = google_bigquery_table.events_view.table_id
  }
}

resource "google_bigquery_dataset_iam_member" "analysts" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.shared.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:${var.analyst_group}"
}
```

## Pitfalls

- `default_kms_key_name` on `google_storage_bucket` goes inside an `encryption {}` block; top-level fails validation.
- The GCS/BigQuery/Cloud Storage service agent needs `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the CMEK key, or writes fail. KMS key location must match the bucket/dataset location.
- Locking a retention policy is permanent; a locked bucket with retention can't be deleted until objects age out.
- UBLA disables object ACLs; after 90 days it can't be reverted. PAP `enforced` blocks `allUsers` bindings, including intended website hosting.
- Versioning without a `num_newer_versions` / noncurrent-age lifecycle rule grows cost unbounded.
- `latest` secret version + a bad rotation = outage; disable (not destroy) old versions first so you can roll back.
- Secret `rotation` needs `next_rotation_time` and a `topics` block; it does not rotate the value itself.
- Mixing `google_bigquery_dataset.access` inline blocks with `google_bigquery_dataset_access` / `_iam_*` resources causes perpetual diffs; pick one.
- Authorized view must live in a different dataset than its source, and the view's own dataset readers still need no access to the source.
- `maximum_bytes_billed` is rounded by billing minimums and does not apply to reservation/slot cost; it caps bytes, not slot time.
- `deletion_protection = true` on tables blocks `terraform destroy` — intended; set false deliberately.
- `require_partition_filter` breaks views/queries that don't filter on the partition column (the view above filters on `event_ts`).

## Verification

```bash
terraform fmt -check && terraform init -backend=false && terraform validate
# against a real project (unverified):
gcloud storage buckets describe gs://$PROJECT-data \
  --format='yaml(uniform_bucket_level_access,public_access_prevention,versioning,retention_policy,default_kms_key,lifecycle_config)'
gcloud secrets get-iam-policy db-password
gcloud secrets describe db-password --format='yaml(rotation,topics)'
bq show --format=prettyjson $PROJECT:private_raw | jq .access
bq query --use_legacy_sql=false --maximum_bytes_billed=1 'SELECT * FROM `p.private_raw.events`'  # expect billing-limit error
```
