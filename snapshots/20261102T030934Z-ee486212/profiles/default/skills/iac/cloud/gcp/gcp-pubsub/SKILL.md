---
name: gcp-pubsub
description: "Use when the task involves Google Cloud Pub/Sub: topics, pull/push/BigQuery subscriptions, dead-letter, retry, ordering, exactly-once, schemas, IAM, CMEK, snapshots/seek"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, pubsub, messaging, terraform, gcloud, iac]
    related_skills: [terraform-infrastructure, cloud-architect]
---

# GCP Pub/Sub

## Overview

Publishers write to a **topic**; each **subscription** on the topic receives its own copy of every message. This skill covers topic/subscription design, reliability features, security, and replay, with gcloud and Terraform.

Verification status: the Terraform below passed `terraform fmt -check` and `terraform validate` (provider `google ~> 6.0`, `init -backend=false`, no apply). **All gcloud commands are UNVERIFIED** (not run against a live project); confirm flags with `gcloud pubsub <cmd> --help`.

## When to Use

- Creating or reviewing topics/subscriptions in Terraform or gcloud
- Adding dead-lettering, retry backoff, ordering, or exactly-once delivery
- Locking down IAM or enabling CMEK
- Replaying messages (seek/snapshot) or debugging stuck/duplicated delivery

## Core Concepts

| Item | Notes |
|---|---|
| Topic | Optional schema, CMEK key, `message_retention_duration` (10m-31d) |
| Pull sub | Client pulls/streams and acks within ack deadline (10-600s) |
| Push sub | Pub/Sub POSTs to an HTTPS endpoint; 2xx = ack. Use an OIDC token for auth |
| BigQuery sub | Writes straight to a table; no consumer code. Needs `use_topic_schema` or `write_metadata` |
| Sub retention | 10m-7d (default 7d); `retain_acked_messages` allows seeking to the past |
| Expiration | Subs expire after 31 days idle by default; `ttl = ""` means never |

## gcloud (UNVERIFIED)

```bash
# Schema + topic with CMEK and retention
gcloud pubsub schemas create orders-schema --type=avro --definition-file=order.avsc
gcloud pubsub topics create orders \
  --schema=orders-schema --message-encoding=json \
  --topic-encryption-key=projects/P/locations/L/keyRings/R/cryptoKeys/K \
  --message-retention-duration=1d

# Pull sub: ordering, exactly-once, retry, dead-letter
gcloud pubsub topics create orders-dlq
gcloud pubsub subscriptions create orders-pull --topic=orders \
  --ack-deadline=60 --enable-message-ordering \
  --enable-exactly-once-delivery \
  --min-retry-delay=10s --max-retry-delay=600s \
  --dead-letter-topic=orders-dlq --max-delivery-attempts=5 \
  --expiration-period=never

# Push sub with OIDC
gcloud pubsub subscriptions create orders-push --topic=orders \
  --push-endpoint=https://example.com/pubsub \
  --push-auth-service-account=worker@P.iam.gserviceaccount.com \
  --push-auth-token-audience=https://example.com/pubsub

# BigQuery sub
gcloud pubsub subscriptions create orders-bq --topic=orders \
  --bigquery-table=P:analytics.orders --use-topic-schema

# Per-resource IAM
gcloud pubsub topics add-iam-policy-binding orders \
  --member=serviceAccount:pub@P.iam.gserviceaccount.com --role=roles/pubsub.publisher
gcloud pubsub subscriptions add-iam-policy-binding orders-pull \
  --member=serviceAccount:worker@P.iam.gserviceaccount.com --role=roles/pubsub.subscriber

# Snapshots / seek
gcloud pubsub snapshots create orders-snap --subscription=orders-pull
gcloud pubsub subscriptions seek orders-pull --snapshot=orders-snap
gcloud pubsub subscriptions seek orders-pull --time=2026-10-18T00:00:00Z
```

## Terraform (validated)

```hcl
terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}

variable "project_id" { type = string }
variable "kms_key_id" { type = string }
variable "worker_sa" { type = string }

data "google_project" "this" { project_id = var.project_id }

locals {
  pubsub_sa = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_schema" "orders" {
  name = "orders-schema"
  type = "AVRO"
  definition = jsonencode({
    type   = "record", name = "Order",
    fields = [{ name = "id", type = "string" }, { name = "amount", type = "double" }]
  })
}

resource "google_pubsub_topic" "orders" {
  name                       = "orders"
  kms_key_name               = var.kms_key_id
  message_retention_duration = "86400s"
  schema_settings {
    schema   = google_pubsub_schema.orders.id
    encoding = "JSON"
  }
  depends_on = [google_pubsub_schema.orders]
}

resource "google_pubsub_topic" "orders_dlq" {
  name = "orders-dlq"
}

resource "google_pubsub_subscription" "orders_pull" {
  name                         = "orders-pull"
  topic                        = google_pubsub_topic.orders.id
  ack_deadline_seconds         = 60
  message_retention_duration   = "604800s"
  retain_acked_messages        = false
  enable_message_ordering      = true
  enable_exactly_once_delivery = true
  expiration_policy { ttl = "" }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.orders_dlq.id
    max_delivery_attempts = 5
  }
}

# Dead-lettering needs the Pub/Sub service agent: publisher on DLQ, subscriber on source sub
resource "google_pubsub_topic_iam_member" "dlq_pub" {
  topic  = google_pubsub_topic.orders_dlq.name
  role   = "roles/pubsub.publisher"
  member = local.pubsub_sa
}

resource "google_pubsub_subscription_iam_member" "src_sub" {
  subscription = google_pubsub_subscription.orders_pull.name
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_sa
}

resource "google_pubsub_subscription_iam_member" "worker" {
  subscription = google_pubsub_subscription.orders_pull.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.worker_sa}"
}

resource "google_pubsub_subscription" "orders_push" {
  name  = "orders-push"
  topic = google_pubsub_topic.orders.id
  push_config {
    push_endpoint = "https://example.com/pubsub"
    oidc_token {
      service_account_email = var.worker_sa
      audience              = "https://example.com/pubsub"
    }
  }
}

resource "google_pubsub_subscription" "orders_bq" {
  name  = "orders-bq"
  topic = google_pubsub_topic.orders.id
  bigquery_config {
    table            = "${var.project_id}.analytics.orders"
    use_topic_schema = true
    write_metadata   = false
  }
}
```

Not in the validated block: CMEK key grant (add `google_kms_crypto_key_iam_member` giving the Pub/Sub service agent `roles/cloudkms.cryptoKeyEncrypterDecrypter`), BigQuery table grant, snapshots (`google_pubsub_snapshot` is not shown here).

## Feature Notes

- **Dead letter:** after `max_delivery_attempts` (5-100) the message goes to the DLQ topic. Service agent `service-<PROJECT_NUMBER>@gcp-sa-pubsub.iam.gserviceaccount.com` needs `publisher` on the DLQ topic and `subscriber` on the source subscription. Attach a subscription to the DLQ topic, otherwise dead-lettered messages are not retained.
- **Retry policy:** exponential backoff between min/max (0-600s) on nack or deadline expiry. Without it, redelivery is immediate.
- **Ordering:** requires an `ordering_key` on publish AND `enable_message_ordering` on the sub. Order holds per key within a region (use regional endpoints). A failed publish blocks that key until the publisher calls resume.
- **Exactly-once:** pull subscriptions only, within a region. Use ack-with-response client APIs and handle failed acks (message may be redelivered). Higher ack latency.
- **Schemas:** AVRO or PROTOCOL_BUFFER; JSON or BINARY encoding; validated at publish time. A schema cannot be deleted while a topic references it.
- **CMEK:** the service agent needs the encrypter/decrypter role on the key; disabling or destroying the key breaks publish/delivery.
- **IAM:** bind at topic/subscription level, not project. Roles: `publisher`, `subscriber`, `viewer`, `editor`. BigQuery sub: service agent needs `roles/bigquery.dataEditor` on the table/dataset (and `metadataViewer`). Push OIDC: the principal creating the sub needs `iam.serviceAccounts.actAs` on the push SA.
- **Retention & seek:** topic retention lets a sub seek to before its creation; `retain_acked_messages` allows replay of acked messages. A snapshot captures the ack state and backlog and lives at most 7 days. Seek redelivers everything after the target, including already-processed messages.

## Pitfalls

1. DLQ IAM missing: messages keep retrying and never move; check the service agent bindings first.
2. No subscription on the DLQ topic: dead-lettered messages are dropped.
3. New subscriptions only see messages published after creation (unless topic retention + seek).
4. Default 31-day idle expiry silently deletes subs; set `expiration_policy { ttl = "" }`.
5. Ack deadline shorter than processing time causes duplicates. Delivery is at-least-once unless exactly-once is on; keep consumers idempotent.
6. Ordering without an `ordering_key` does nothing, and it limits per-key throughput.
7. Destroying a schema before its topic fails; keep `depends_on`/references so Terraform orders it.
8. Push endpoints must be HTTPS and answer fast; slow replies cause redelivery storms.
9. Message size limit is 10 MB; batch publishes for throughput.
10. BigQuery sub write failures (schema mismatch, missing permissions) retry or go to the DLQ if configured.
11. Changing `enable_message_ordering`/exactly-once semantics on existing subs: check the provider/API docs for immutability before applying.

## Verification

```bash
cd tf-dir && terraform fmt -check && terraform init -backend=false && terraform validate
gcloud pubsub topics describe orders
gcloud pubsub subscriptions describe orders-pull   # deadLetterPolicy, retryPolicy, enableMessageOrdering, enableExactlyOnceDelivery
gcloud pubsub topics get-iam-policy orders
gcloud pubsub subscriptions get-iam-policy orders-pull
gcloud pubsub topics publish orders --message='{"id":"1","amount":1.5}'
gcloud pubsub subscriptions pull orders-pull --auto-ack --limit=1
```
Monitor `subscription/oldest_unacked_message_age` and `subscription/dead_letter_message_count` in Cloud Monitoring.
