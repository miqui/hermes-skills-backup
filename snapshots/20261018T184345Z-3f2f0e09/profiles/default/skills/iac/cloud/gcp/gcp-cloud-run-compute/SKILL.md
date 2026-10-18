---
name: gcp-cloud-run-compute
description: "Use when deploying or hardening GCP Cloud Run services/jobs, Compute Engine VMs, or Artifact Registry. Gives gcloud and Terraform (google provider) baselines."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, iac, cloud-run, compute-engine, artifact-registry, terraform, gcloud, security]
    related_skills: [terraform-infrastructure, cloud-architect, terraform-skill]
---

# GCP Cloud Run, Compute Engine, Artifact Registry

## Overview

Secure-by-default baselines for container and VM compute on Google Cloud, each shown with `gcloud` and Terraform (`hashicorp/google` provider). Flags marked **(unverified)** were not checked against `--help` or `terraform validate`; everything else was.

## When to Use

- Deploy/update a Cloud Run service or job, or lock down its ingress, identity, and secrets.
- Create a Compute Engine VM with Shielded VM, OS Login, and no external IP.
- Create an Artifact Registry repo and wire push/pull IAM.
- Do NOT use for GKE (use a Kubernetes skill) or for apply-time org policy changes without review.

## Procedure

1. Confirm target: `gcloud config list` and `gcloud auth list`; never rely on an implicit default project.
2. Enable APIs: `gcloud services enable run.googleapis.com compute.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com`
3. Create a dedicated service account per workload (never the default compute SA).
4. Create the Artifact Registry repo, push the image, then deploy by digest.
5. Run `terraform fmt -check && terraform validate`, then `terraform plan`, before any apply.

### Artifact Registry

```bash
gcloud artifacts repositories create app-images \
  --repository-format=docker --location=us-central1 \
  --immutable-tags --description="App images"
gcloud auth configure-docker us-central1-docker.pkg.dev
docker push us-central1-docker.pkg.dev/$PROJECT/app-images/api:1.0.0
# Grant pull to the runtime SA (repo-scoped, not project-wide)
gcloud artifacts repositories add-iam-policy-binding app-images --location=us-central1 \
  --member="serviceAccount:api-sa@$PROJECT.iam.gserviceaccount.com" --role=roles/artifactregistry.reader
```

```hcl
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "app-images"
  format        = "DOCKER"
  docker_config {
    immutable_tags = true
  }
}

resource "google_artifact_registry_repository_iam_member" "runtime_reader" {
  location   = google_artifact_registry_repository.app.location
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.api.email}"
}
```

### Cloud Run service

```bash
gcloud run deploy api \
  --image=us-central1-docker.pkg.dev/$PROJECT/app-images/api@sha256:<digest> \
  --region=us-central1 --service-account=api-sa@$PROJECT.iam.gserviceaccount.com \
  --no-allow-unauthenticated --ingress=internal-and-cloud-load-balancing \
  --min-instances=0 --max-instances=10 \
  --set-secrets=DB_PASSWORD=db-password:latest
# Grant a caller (private service)
gcloud run services add-iam-policy-binding api --region=us-central1 \
  --member="serviceAccount:caller@$PROJECT.iam.gserviceaccount.com" --role=roles/run.invoker
```

```hcl
resource "google_service_account" "api" {
  account_id   = "api-sa"
  display_name = "Cloud Run api runtime"
}

resource "google_cloud_run_v2_service" "api" {
  name                = "api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  deletion_protection = true

  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = var.image # pin by digest
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.db_secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "invoker" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.caller_sa_email}"
}
```

### Cloud Run job

```bash
gcloud run jobs create nightly --image=$IMAGE --region=us-central1 \
  --service-account=job-sa@$PROJECT.iam.gserviceaccount.com \
  --tasks=1 --max-retries=2 --task-timeout=15m
gcloud run jobs execute nightly --region=us-central1 --wait
```

```hcl
resource "google_cloud_run_v2_job" "nightly" {
  name                = "nightly"
  location            = var.region
  deletion_protection = true
  template {
    task_count = 1
    template {
      service_account = google_service_account.job.email
      max_retries     = 2
      timeout         = "900s"
      containers {
        image = var.image
      }
    }
  }
}
```

### Compute Engine baseline (Shielded VM, OS Login, no external IP)

```bash
gcloud compute instances create app-vm --zone=us-central1-a --machine-type=e2-small \
  --image-family=debian-12 --image-project=debian-cloud \
  --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
  --no-address --network=default --subnet=default \
  --metadata=enable-oslogin=TRUE,block-project-ssh-keys=TRUE \
  --service-account=vm-sa@$PROJECT.iam.gserviceaccount.com --scopes=cloud-platform
# Access without a public IP: IAP tunnel + OS Login (needs roles/compute.osLogin and IAP-secured Tunnel User)
gcloud compute ssh app-vm --zone=us-central1-a --tunnel-through-iap
# Egress for package installs needs Cloud NAT (no external IP != no internet)
```

```hcl
resource "google_compute_instance" "app" {
  name         = "app-vm"
  zone         = "${var.region}-a"
  machine_type = "e2-small"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork
    # no access_config block => no external IP
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata = {
    enable-oslogin         = "TRUE"
    block-project-ssh-keys = "TRUE"
  }

  service_account {
    email  = google_service_account.vm.email
    scopes = ["cloud-platform"]
  }
}
```

Org-level guardrails (review before applying): constraints `compute.requireOsLogin`, `compute.requireShieldedVm`, `compute.vmExternalIpAccess` **(constraint names unverified here)**.

## Pitfalls

- `--no-allow-unauthenticated` still permits any caller holding `roles/run.invoker`; never bind `allUsers` unless intended public.
- Cloud Run `ingress=internal` blocks browser/public traffic, and also calls from outside the VPC/Google-internal paths; pick the weakest setting that works.
- Tags like `:latest` drift; deploy by digest. `immutable_tags` makes re-pushing a tag fail, so CI must use unique tags.
- Secrets: pass via Secret Manager refs, never `--set-env-vars`; the runtime SA needs `roles/secretmanager.secretAccessor`.
- Defaults to the Compute default SA with Editor role are over-privileged; always set a dedicated SA.
- No external IP means no outbound internet and no Artifact Registry reach unless Private Google Access or Cloud NAT is on.
- OS Login needs IAM roles (`roles/compute.osLogin`/`osAdminLogin`); metadata SSH keys are ignored once enabled.
- Shielded VM requires a Shielded-capable image (current Debian/Ubuntu/Windows are); custom images may not boot with Secure Boot.
- Terraform: `google_cloud_run_v2_*` sets `deletion_protection=true` by default in recent providers; destroy fails until it is set false and applied. Don't use the deprecated `google_cloud_run_service` for new work.
- Terraform changes to `template.containers.image` by CI cause drift; add `lifecycle { ignore_changes = [...] }` only if CI owns deploys.

## Verification

- `gcloud run services describe api --region=us-central1 --format='value(spec.template.spec.serviceAccountName,metadata.annotations)'`
- `gcloud compute instances describe app-vm --zone=us-central1-a --format=yaml(shieldedInstanceConfig,networkInterfaces[].accessConfigs,metadata.items)` — expect no `accessConfigs`.
- `terraform fmt -check -recursive && terraform validate` (no apply).
