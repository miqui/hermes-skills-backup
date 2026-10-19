---
name: gcp-cloud-functions
description: "Use when the task involves Cloud Functions 2nd gen on GCP. Deploys and debugs Cloud Run-based functions with HTTP, Pub/Sub and Eventarc triggers, per-function service accounts, VPC connector or Direct VPC egress, Secret Manager, ingress settings, and min/max instances, using gcloud and Terraform (google provider). Use when the user mentions Cloud Functions, gen2, Eventarc, function 403/cold start/timeouts, or serverless VPC access. Do NOT use for plain Cloud Run services, App Engine, or GKE."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, iac, cloud-functions, cloud-run, eventarc, pubsub, serverless, terraform]
    related_skills: [terraform-infrastructure, cloud-architect]
---

# GCP Cloud Functions (2nd gen)

## Overview

2nd gen functions are Cloud Run services built by Cloud Build and stored in Artifact Registry, with Eventarc providing event triggers. Each function = one Cloud Run service (same name) + optional Eventarc trigger. Many knobs (concurrency, CPU, revisions, IAM) are therefore Cloud Run knobs. Always pass `--gen2` (gcloud) or use `google_cloudfunctions2_function` (Terraform); 1st gen is legacy.

## When to Use

- Deploying/updating event-driven or HTTP functions on GCP
- Debugging 403 invocations, triggers not firing, build failures, cold starts, egress to private IPs
- Writing Terraform for functions with secrets, VPC, and least-privilege identities

## Core rules

1. **One dedicated service account per function** (runtime identity). Never leave the default compute SA (Editor role) in place. Grant only needed roles.
2. **Separate identities**: runtime SA (`--run-service-account`), trigger SA (`--trigger-service-account`, needs `roles/run.invoker` on the service and `roles/eventarc.eventReceiver`), and the build SA (project-dependent Cloud Build/Artifact Registry rights).
3. Keep functions private (`--no-allow-unauthenticated`, the default); invoke with identity tokens.
4. Pin runtime, region, and source; keep credentials in Secret Manager, not plain env vars.

## gcloud examples

Flag names were checked against local `gcloud functions deploy --help`; the commands were not executed against a project.

```bash
PROJECT=my-proj; REGION=us-central1
gcloud services enable cloudfunctions.googleapis.com run.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com \
  eventarc.googleapis.com pubsub.googleapis.com secretmanager.googleapis.com

gcloud iam service-accounts create fn-orders-sa --display-name="orders function"

# HTTP: private, limits, secret env var, VPC connector
gcloud functions deploy orders-http --gen2 --region=$REGION --runtime=python312 \
  --source=. --entry-point=handler --trigger-http --no-allow-unauthenticated \
  --run-service-account=fn-orders-sa@$PROJECT.iam.gserviceaccount.com \
  --ingress-settings=internal-and-gclb \
  --min-instances=1 --max-instances=20 --concurrency=40 --cpu=1 --memory=512Mi \
  --timeout=60s \
  --set-secrets="DB_PASS=db-pass:latest" \
  --vpc-connector=projects/$PROJECT/locations/$REGION/connectors/my-conn \
  --egress-settings=private-ranges-only

# Pub/Sub trigger (Eventarc manages the subscription)
gcloud functions deploy orders-sub --gen2 --region=$REGION --runtime=python312 \
  --source=. --entry-point=on_msg --trigger-topic=orders \
  --run-service-account=fn-orders-sa@$PROJECT.iam.gserviceaccount.com \
  --trigger-service-account=fn-orders-trigger@$PROJECT.iam.gserviceaccount.com \
  --retry

# Eventarc: Cloud Storage finalized (trigger location must match bucket location)
gcloud functions deploy on-upload --gen2 --region=$REGION --runtime=python312 \
  --source=. --entry-point=on_obj \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=my-bucket" --trigger-location=$REGION

# Direct VPC egress (flags exist; exact value syntax UNVERIFIED - run --help)
gcloud functions deploy orders-http --gen2 --region=$REGION \
  --network=my-vpc --subnet=my-subnet --direct-vpc-egress=all-traffic  # UNVERIFIED values

# Let a caller invoke (run.invoker on the underlying Cloud Run service)
gcloud run services add-iam-policy-binding orders-http --region=$REGION \
  --member=serviceAccount:caller@$PROJECT.iam.gserviceaccount.com --role=roles/run.invoker

URL=$(gcloud functions describe orders-http --gen2 --region=$REGION --format='value(serviceConfig.uri)')
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" "$URL"
```

## Terraform (google provider)

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

resource "google_service_account" "fn" {
  project      = var.project
  account_id   = "fn-orders-sa"
  display_name = "orders function runtime"
}

resource "google_secret_manager_secret" "db" {
  project   = var.project
  secret_id = "db-pass"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "fn" {
  project   = var.project
  secret_id = google_secret_manager_secret.db.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.fn.email}"
}

resource "google_storage_bucket" "src" {
  project                     = var.project
  name                        = "${var.project}-fn-src"
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "zip" {
  name   = "orders-${filemd5("fn.zip")}.zip" # hash in name forces redeploy on change
  bucket = google_storage_bucket.src.name
  source = "fn.zip"
}

resource "google_pubsub_topic" "orders" {
  project = var.project
  name    = "orders"
}

resource "google_cloudfunctions2_function" "orders" {
  project  = var.project
  name     = "orders-sub"
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "on_msg"
    source {
      storage_source {
        bucket = google_storage_bucket.src.name
        object = google_storage_bucket_object.zip.name
      }
    }
  }

  service_config {
    service_account_email            = google_service_account.fn.email
    min_instance_count               = 0
    max_instance_count               = 20
    max_instance_request_concurrency = 40
    available_memory                 = "512Mi"
    available_cpu                    = "1"
    timeout_seconds                  = 60
    ingress_settings                 = "ALLOW_INTERNAL_ONLY"
    vpc_connector                    = "projects/${var.project}/locations/${var.region}/connectors/my-conn"
    vpc_connector_egress_settings    = "PRIVATE_RANGES_ONLY"

    secret_environment_variables {
      key        = "DB_PASS"
      project_id = var.project
      secret     = google_secret_manager_secret.db.secret_id
      version    = "latest"
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.orders.id
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.fn.email
  }

  depends_on = [google_secret_manager_secret_iam_member.fn]
}

# Grant invoker on the underlying Cloud Run service (needed for HTTP callers
# and for the event trigger SA)
resource "google_cloud_run_service_iam_member" "invoker" {
  project  = var.project
  location = google_cloudfunctions2_function.orders.location
  service  = google_cloudfunctions2_function.orders.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.fn.email}"
}
```

Direct VPC egress in Terraform: whether `google_cloudfunctions2_function` exposes it depends on provider version (UNVERIFIED); otherwise use `vpc_connector`, gcloud, or a Cloud Run v2 service.

## Pitfalls

- **Ingress** values: `ALLOW_ALL`, `ALLOW_INTERNAL_ONLY`, `ALLOW_INTERNAL_AND_GCLB`. Internal-only rejects internet callers and non-VPC sources; retest Scheduler/other-project callers after changing.
- **Public access** needs `allUsers` with `roles/run.invoker`; org policy (domain-restricted sharing) can block it.
- **403 on event delivery**: trigger SA lacks `run.invoker`/`eventarc.eventReceiver`, or Pub/Sub service agent lacks token-creator rights (older projects).
- **Build failures**: build SA or Artifact Registry permissions; new projects with restricted default compute SA are a common cause.
- **Secrets**: `latest` is resolved at instance start; deploy a new revision to pick up changes. Runtime SA needs `secretAccessor`. Use pinned versions for reproducibility.
- **VPC connector** needs a /28 range, is regional, and bills always-on instances; `private-ranges-only` sends public traffic over the internet, `all-traffic` needs Cloud NAT for internet. Direct VPC egress avoids connector VMs but needs subnet IP capacity.
- **min-instances > 0** bills idle; too-low **max-instances** causes 429s. Event delivery is at-least-once: make handlers idempotent.
- **Retry** on event functions redelivers failing events for a long window; poison messages loop unless you ack-and-log or use a dead-letter topic.
- **Concurrency > 1** shares globals across requests; set `--concurrency=1` for non-thread-safe code. CPU below 1 vCPU forces concurrency 1.
- **Timeouts**: HTTP and event-driven limits differ (verify current quotas).
- **Terraform**: unchanged zip object name means no redeploy; renaming a function recreates it; Eventarc trigger region must match the source (e.g. GCS bucket location).
- No in-place gen1 to gen2 upgrade under the same name; deploy new and cut over.

## Verification

```bash
gcloud functions describe orders-http --gen2 --region=$REGION \
  --format='yaml(state,serviceConfig.serviceAccountEmail,serviceConfig.ingressSettings,serviceConfig.minInstanceCount,serviceConfig.maxInstanceCount,serviceConfig.vpcConnector,eventTrigger)'
gcloud functions logs read orders-http --gen2 --region=$REGION --limit=50
gcloud run services get-iam-policy orders-http --region=$REGION
terraform fmt -check && terraform init -backend=false && terraform validate
```

Expect `state: ACTIVE`, a dedicated SA (not `-compute@developer`), unauthenticated curl returns 403 on private functions, authenticated call returns 200.
