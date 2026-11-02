---
name: gcp-iam-auth
description: "Use when configuring GCP authentication or IAM: service accounts, Workload Identity Federation for keyless CI, least-privilege roles, org policies, gcloud/ADC. Gives verified gcloud and Terraform patterns plus pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, iam, auth, workload-identity-federation, service-accounts, terraform, security]
    related_skills: [terraform-infrastructure, cloud-architect, github-actions-ci]
---

# GCP IAM & Auth

Security-first patterns for identities and credentials on Google Cloud. Preference order: **no credential > short-lived token > long-lived key**.

## When to Use

- Creating/auditing service accounts (SAs) and role bindings
- Wiring CI (GitHub Actions, GitLab, etc.) to GCP without SA keys (Workload Identity Federation, WIF)
- Choosing least-privilege roles, writing org policy constraints
- Debugging `gcloud auth` vs Application Default Credentials (ADC) confusion, 403s, quota-project errors

Verify mutable facts (role names, constraints, provider versions) against current docs; commands below were checked against `gcloud` 586.0.0 `--help` output and Terraform snippets with `terraform validate` (google provider ~> 6.0). Nothing was applied to a real project.

## Core model

- **Principal** (user, group, SA, federated principal) + **role** + **resource** = binding, in an IAM policy attached at org/folder/project/resource. Policies are inherited downward and are additive (allow); deny policies and org policies restrict.
- An SA is both a *principal* (can be granted roles) and a *resource* (others get roles on it, e.g. `roles/iam.serviceAccountUser`, `roles/iam.workloadIdentityUser`, `roles/iam.serviceAccountTokenCreator`).
- Prefer one SA per workload, created in a dedicated project; name by function (`ci-deployer`), never reuse default compute/App Engine SAs.

## Service accounts (gcloud)

```bash
PROJECT_ID=my-project   # placeholder
gcloud iam service-accounts create ci-deployer \
  --project="$PROJECT_ID" --display-name="CI deployer"

# Grant a narrow predefined role on the narrowest resource
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.developer" --condition=None

# Audit: who can impersonate/use this SA, and any user-managed keys
gcloud iam service-accounts get-iam-policy "ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts keys list \
  --iam-account="ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com" --managed-by=user
```

### Impersonation instead of keys (local dev)

```bash
# Needs roles/iam.serviceAccountTokenCreator on the SA
gcloud config set auth/impersonate_service_account ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com
# or per command:
gcloud storage ls --impersonate-service-account=ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com
# ADC for client libraries/Terraform, acting as the SA:
gcloud auth application-default login --impersonate-service-account=ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com
```

## Keyless CI with Workload Identity Federation (GitHub Actions)

```bash
PROJECT_NUMBER=123456789012; REPO=owner/repo   # placeholders
gcloud iam workload-identity-pools create github-pool \
  --project="$PROJECT_ID" --location=global

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project="$PROJECT_ID" --location=global --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='${REPO}' && assertion.ref=='refs/heads/main'"

# Let ONLY that repo's identities impersonate the SA
gcloud iam service-accounts add-iam-policy-binding \
  "ci-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"
```

Workflow (uses `google-github-actions/auth`; pin to a commit SHA in real use, check the current major version):

```yaml
permissions:
  contents: read
  id-token: write        # required to mint the OIDC token
steps:
  - uses: google-github-actions/auth@<pinned-sha>
    with:
      workload_identity_provider: projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/providers/github-provider
      service_account: ci-deployer@<PROJECT_ID>.iam.gserviceaccount.com
```

Non-GitHub/local test: `gcloud iam workload-identity-pools create-cred-config` generates the external-account credential config (no secret inside); `gcloud auth login --cred-file=...` uses it.

## Terraform (google provider)

Validated with `terraform fmt` + `terraform validate`:

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" { type = string }
variable "project_number" { type = string }
variable "github_repo" {
  type        = string
  description = "owner/repo allowed to deploy"
}

resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = "ci-deployer"
  display_name = "CI deployer (keyless)"
}

# Least privilege: narrow predefined role, on the narrowest resource.
resource "google_project_iam_member" "deployer_run" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = google_service_account.deployer.member
}

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }
  # Never leave unrestricted: any GitHub repo on earth issues tokens from this issuer.
  attribute_condition = "assertion.repository == '${var.github_repo}' && assertion.ref == 'refs/heads/main'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_repo}"
}

# Org policy v2: block SA key creation
resource "google_org_policy_policy" "no_sa_keys" {
  name   = "projects/${var.project_id}/policies/iam.disableServiceAccountKeyCreation"
  parent = "projects/${var.project_id}"
  spec {
    rules {
      enforce = "TRUE"
    }
  }
}
```

Terraform tips: prefer `google_*_iam_member` (additive) over `_iam_binding` (authoritative per role) and avoid `_iam_policy` (replaces whole policy; can lock you out). Run Terraform itself via ADC/impersonation or WIF, not a downloaded key.

## Least-privilege roles

1. Never use basic roles (`roles/owner`, `editor`, `viewer`) for workloads; `editor` is broad and grants most data-plane write access.
2. Pick the smallest predefined role (`gcloud iam roles describe roles/run.developer` lists permissions); bind at resource level (bucket, secret, dataset) when possible.
3. If none fits, create a custom role (`gcloud iam roles create NAME --project=$PROJECT_ID --file=role.yaml`) with only needed permissions.
4. Use IAM Conditions (`--condition=expression=...,title=...`) for time/resource scoping.
5. Review with IAM Recommender: `gcloud recommender recommendations list --recommender=google.iam.policy.Recommender --project=$PROJECT_ID --location=global`.
6. Dangerous grants to treat as privilege escalation: `iam.serviceAccountTokenCreator`, `iam.serviceAccountUser` (project-wide), `iam.serviceAccountKeyAdmin`, `resourcemanager.projectIamAdmin`, `setIamPolicy` permissions generally.

## Org policies

Useful constraints (check current names in the constraint list):

- `iam.disableServiceAccountKeyCreation` — block user-managed keys (also consider `iam.disableServiceAccountKeyUpload`)
- `iam.automaticIamGrantsForDefaultServiceAccounts` — stop auto-granting Editor to default SAs
- `iam.allowedPolicyMemberDomains` — restrict principals to your Cloud Identity domain(s)
- `iam.workloadIdentityPoolProviders` / `iam.workloadIdentityPoolAwsAccounts` — allowlist external IdPs

```bash
gcloud org-policies set-policy policy.yaml   # YAML with name + spec.rules (v2 API)
gcloud org-policies describe iam.disableServiceAccountKeyCreation --project=$PROJECT_ID
```

Setting org policies needs `roles/orgpolicy.policyAdmin`; check `gcloud org-policies describe --effective` and audit existing key usage before enforcing org-wide, since enforcement can break existing key-based pipelines.

## gcloud auth vs ADC

Two **separate** credential stores:

| | `gcloud auth login` | `gcloud auth application-default login` |
|---|---|---|
| Used by | `gcloud`, `gsutil`, `bq` | Client libraries, Terraform, most SDKs |
| Check | `gcloud auth list` | `gcloud auth application-default print-access-token` |

ADC search order: `GOOGLE_APPLICATION_CREDENTIALS` env var → ADC file from `gcloud auth application-default login` → attached SA from metadata server (GCE/GKE/Cloud Run).

## Pitfalls

- **Logging in with `gcloud auth login` does not set ADC.** Terraform/SDKs still fail or use a different identity. Run both, or use `--update-adc` on login.
- **`GOOGLE_APPLICATION_CREDENTIALS` silently wins** over everything; an old exported path is a top source of "wrong identity". `unset` it and run `gcloud auth list` / check `gcloud config list`.
- **Quota project errors with user ADC** (`API requires a quota project`): `gcloud auth application-default set-quota-project $PROJECT_ID`; caller needs `roles/serviceusage.serviceUsageConsumer`.
- **Unrestricted WIF provider.** Missing/weak `attribute_condition` lets other tenants' tokens through; GitHub-issuer providers require a condition. Match on `repository` (or immutable `repository_id`/owner id), never on org name prefixes alone; also restrict `ref`/environment for deploy roles.
- **`principal://` vs `principalSet://`**: `attribute.X/value` forms use `principalSet`; a single subject uses `principal://.../subject/<sub>`. Binding uses **project number**, not ID.
- **WIF needs `id-token: write`** in the workflow, and fork PRs don't get it — don't loosen conditions to "fix" this.
- **Propagation delay**: IAM changes can take ~minutes (up to ~7 for removals); 403 right after granting is often just lag. Retry before widening roles.
- **`serviceAccountUser` on project** lets a principal run anything as every SA there. Grant per-SA only.
- **Default SAs**: legacy compute/App Engine default SAs may hold Editor. Replace with dedicated SAs and enforce the org policy above.
- **Keys**: if a key is unavoidable, set expiry, store in Secret Manager/CI secret store, rotate, and never commit; delete with `gcloud iam service-accounts keys delete`. Leaked key = full SA access until deleted.
- **Terraform `_iam_binding`/`_iam_policy`** remove members not in config, potentially cutting off Google-managed agents or yourself.
- **Org policy v1 vs v2**: `gcloud resource-manager org-policies` is the legacy v1 surface; use `gcloud org-policies` and `google_org_policy_policy` for new work.
- **`--impersonate-service-account` fails** with 403 unless caller has `iam.serviceAccountTokenCreator` on the SA and the IAM Credentials API is enabled.
- Never paste tokens (`gcloud auth print-access-token`) or key JSON into chat, logs, or commits; use placeholders.
