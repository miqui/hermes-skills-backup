---
name: gcp-observability-cost
description: "Use when configuring GCP logging, monitoring, audit logs, budgets, billing export, labels or recommender. gcloud + Terraform patterns and pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, iac, observability, logging, monitoring, finops, terraform]
    related_skills: [terraform-infrastructure, cloud-architect]
---

# GCP Observability and Cost

## Overview

Covers Cloud Logging (sinks, buckets, exclusions, retention), Cloud Monitoring (alert policies, uptime checks, notification channels), Cloud Audit Logs, billing budgets, labels, billing export to BigQuery, and Recommender. Terraform blocks below were validated (`terraform fmt -check`, `init -backend=false`, `validate`; Terraform 1.16.2, google provider ~> 6.0). gcloud/bq commands are **unverified** (not run against a live project).

## When to Use

- Routing, retaining, or excluding logs; enabling Data Access audit logs.
- Building alerts, uptime checks, and notification channels.
- Setting budgets, billing export, cost labels, or acting on rightsizing/idle recommendations.

## Cloud Logging

- `_Required` bucket (Admin Activity, System Event; 400 days) is immutable and cannot be excluded. `_Default` bucket: 30 days default, configurable.
- Sinks only forward logs written after creation; each sink has a writer identity that needs IAM on the destination.
- Exclusions on the `_Default` sink drop logs before storage (lost forever). Prefer routing to a cheaper bucket if you may need them.

```bash
# unverified
gcloud logging buckets update _Default --location=global --retention-days=14
gcloud logging buckets create app-logs --location=global --retention-days=90
gcloud logging sinks create errors-to-bq \
  bigquery.googleapis.com/projects/PROJECT/datasets/log_sink \
  --log-filter='severity>=ERROR' --use-partitioned-tables
gcloud logging sinks describe errors-to-bq --format='value(writerIdentity)'   # grant IAM on dest
gcloud logging sinks update _Default --add-exclusion=name=drop-debug,filter='severity<=DEBUG'
```

Inputs assumed by the snippets below:

```hcl
variable "project_id" { type = string }
variable "email" { type = string }
variable "billing_account" { type = string }
```

```hcl
resource "google_logging_project_bucket_config" "app" {
  project        = var.project_id
  location       = "global"
  bucket_id      = "app-logs"
  retention_days = 90
}

resource "google_bigquery_dataset" "logs" {
  project    = var.project_id
  dataset_id = "log_sink"
  location   = "US"
}

resource "google_logging_project_sink" "bq" {
  project                = var.project_id
  name                   = "errors-to-bq"
  destination            = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.logs.dataset_id}"
  filter                 = "severity>=ERROR"
  unique_writer_identity = true
  bigquery_options { use_partitioned_tables = true }
}

resource "google_bigquery_dataset_iam_member" "sink_writer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.logs.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.bq.writer_identity
}

resource "google_logging_project_exclusion" "debug" {
  project     = var.project_id
  name        = "drop-debug"
  description = "Drop DEBUG logs"
  filter      = "severity<=DEBUG"
}
```

## Cloud Audit Logs

- Admin Activity: always on, free, cannot be disabled. Data Access (DATA_READ/DATA_WRITE/ADMIN_READ): off by default (BigQuery excepted), billable, can be very noisy.
- Use `exempted_members` inside `audit_log_config` to cut noise from specific principals.

```hcl
resource "google_project_iam_audit_config" "all" {
  project = var.project_id
  service = "allServices"
  audit_log_config { log_type = "ADMIN_READ" }
  audit_log_config { log_type = "DATA_READ" }
  audit_log_config { log_type = "DATA_WRITE" }
}
```

```bash
# unverified: edit auditConfigs in the policy, then set it
gcloud projects get-iam-policy PROJECT --format=yaml > p.yaml
gcloud projects set-iam-policy PROJECT p.yaml
gcloud logging read 'logName:"cloudaudit.googleapis.com%2Fdata_access"' --limit=5 --project=PROJECT
```

## Cloud Monitoring

```hcl
resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "oncall"
  type         = "email"
  labels       = { email_address = var.email }
}

resource "google_monitoring_uptime_check_config" "http" {
  project      = var.project_id
  display_name = "https-check"
  timeout      = "10s"
  period       = "60s"
  http_check {
    path         = "/healthz"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }
  monitored_resource {
    type   = "uptime_url"
    labels = { project_id = var.project_id, host = "example.com" }
  }
}

resource "google_monitoring_alert_policy" "uptime" {
  project               = var.project_id
  display_name          = "uptime-failing"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]
  conditions {
    display_name = "check failing"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.label.check_id=\"${google_monitoring_uptime_check_config.http.uptime_check_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period     = "1200s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.*"]
      }
    }
  }
}
```

```bash
# unverified
gcloud beta monitoring channels create --display-name=oncall --type=email --channel-labels=email_address=a@b.com
gcloud alpha monitoring policies create --policy-from-file=policy.json
gcloud monitoring uptime list-configs
```

## Billing Budgets, Export, Labels

- Budgets only alert; they do NOT cap spend. To stop spend, wire a Pub/Sub topic (`all_updates_rule`) to automation.
- Threshold values are fractions (0.9 = 90%), not percents.
- Billing export to BigQuery has no reliable Terraform resource: enable in Console (Billing > Billing export). It is not retroactive. Standard usage, Detailed usage, and Pricing exports are separate toggles.
- Labels reach the export only for label-capable resources; set via `labels` or provider `default_labels`. Keys lowercase, max 63 chars, max 64 labels per resource.

```hcl
resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account
  display_name    = "monthly"
  budget_filter {
    projects = ["projects/${var.project_id}"]
  }
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "1000"
    }
  }
  threshold_rules { threshold_percent = 0.5 }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }
}
```

```bash
# unverified
gcloud billing budgets create --billing-account=ID --display-name=monthly \
  --budget-amount=1000USD --threshold-rule=percent=0.5 --threshold-rule=percent=0.9
gcloud billing budgets list --billing-account=ID
bq query --use_legacy_sql=false 'SELECT service.description, SUM(cost) c FROM `PROJ.DS.gcp_billing_export_v1_*` GROUP BY 1 ORDER BY c DESC'
```

## Recommender

```bash
# unverified
gcloud services enable recommender.googleapis.com
gcloud recommender recommendations list --project=PROJECT --location=us-central1 \
  --recommender=google.compute.instance.MachineTypeRecommender
gcloud recommender recommendations list --project=PROJECT --location=global \
  --recommender=google.iam.policy.Recommender
```

Other IDs: `google.compute.instance.IdleResourceRecommender`, `google.compute.disk.IdleResourceRecommender`, `google.compute.address.IdleResourceRecommender`.

## Pitfalls

- Sink writer identity needs IAM on the destination or logs silently drop.
- Org/folder sinks need `include_children = true` to capture child projects.
- Data Access logs on `allServices` (esp. GCS/BigQuery reads) can cost more than compute; scope by service and exempt service accounts.
- Exclusions and new sinks are not retroactive.
- Lowering bucket retention deletes older data; deleted buckets linger ~7 days.
- Uptime alert: `REDUCE_COUNT_FALSE` with threshold 1 fires when more than one probe location fails; tune deliberately.
- Slack/PagerDuty channels need auth tokens set outside plain Terraform; email works directly.
- Budgets need `billingbudgets.googleapis.com` enabled; with user credentials set `user_project_override = true` and `billing_project` in the provider.
- Recommender "no results" usually means API disabled, wrong location/recommender ID, or insufficient history.

## Verification

```bash
terraform fmt -check
terraform init -backend=false
terraform validate
gcloud logging sinks list --project=PROJECT                     # unverified
gcloud logging buckets describe app-logs --location=global --format='value(retentionDays)'
gcloud monitoring policies list --project=PROJECT
gcloud billing budgets list --billing-account=ID
```
