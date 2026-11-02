---
name: gcp-gke
description: Use when creating, securing, or operating Google Kubernetes Engine (GKE) clusters. Covers Autopilot vs Standard, private clusters, Workload Identity, release channels, node pools, network policy, and Binary Authorization basics with gcloud, kubectl, and Terraform.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, gke, kubernetes, autopilot, workload-identity, binary-authorization, terraform, gcloud, devops]
    related_skills: [kubernetes, terraform-infrastructure, terraform-skill, cloud-architect]
---

# GCP GKE

## Overview

GKE-specific decisions and commands. For generic workload debugging use the `kubernetes` skill; for Terraform workflow use `terraform-infrastructure`. Commands marked **(unverified)** were not run against a live project; flags change between gcloud releases, so confirm with `gcloud container clusters create --help` first.

## When to Use

- Choosing Autopilot vs Standard, or creating/upgrading a GKE cluster
- Making a cluster private, enabling Workload Identity, network policy, or Binary Authorization
- Managing release channels, maintenance windows, node pools
- Writing `google_container_cluster` / `google_container_node_pool` Terraform

## Preflight

```bash
gcloud config list                         # confirm project/account before ANY change
gcloud services enable container.googleapis.com compute.googleapis.com
gcloud container get-server-config --region us-central1 --format="yaml(channels)"
```

## Autopilot vs Standard

| | Autopilot | Standard |
|---|---|---|
| Nodes | Google-managed, no node pools to manage | You manage node pools |
| Billing | Per pod resource requests | Per node VM |
| Hardening | Workload Identity, shielded nodes, private-capable by default; no privileged pods, no SSH to nodes | Opt in to each |
| Fit | Most stateless/web workloads | Custom kernels/DaemonSets needing privilege, specific machine families, tight cost tuning |
| Release channel | Always enrolled (required) | Optional but recommended |

Default to Autopilot unless a concrete need (privileged DaemonSet, unsupported hardware) rules it out. Autopilot vs Standard cannot be switched in place; migration = new cluster.

## Create clusters (gcloud)

```bash
# Autopilot, private nodes, regional
gcloud container clusters create-auto demo-auto \
  --region us-central1 \
  --release-channel regular \
  --enable-private-nodes \
  --network default --subnetwork default

# Standard, private, Workload Identity, network policy, shielded nodes (unverified flag set)
gcloud container clusters create demo-std \
  --region us-central1 \
  --release-channel regular \
  --num-nodes 1 \
  --enable-ip-alias \
  --enable-private-nodes --master-ipv4-cidr 172.16.0.0/28 \
  --enable-master-authorized-networks --master-authorized-networks 203.0.113.0/24 \
  --workload-pool=PROJECT_ID.svc.id.goog \
  --enable-shielded-nodes \
  --shielded-secure-boot --shielded-integrity-monitoring \
  --enable-network-policy        # or --enable-dataplane-v2 (mutually exclusive)

gcloud container clusters get-credentials demo-std --region us-central1
kubectl get nodes
```

## Private clusters

- Private nodes have no public IPs; egress to the internet needs **Cloud NAT** on the VPC/region.
- Control-plane endpoint: keep public endpoint restricted with `--master-authorized-networks`, or use `--enable-private-endpoint` (then only reachable from the VPC/peered/VPN/bastion).
- Use `--enable-ip-alias` (VPC-native); required for private clusters.
- Pods pulling from Artifact Registry use Private Google Access (enable on the subnet) when no NAT.

```bash
gcloud compute routers create nat-router --network default --region us-central1
gcloud compute routers nats create nat-cfg --router nat-router --region us-central1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
gcloud container clusters update demo-std --region us-central1 \
  --enable-master-authorized-networks --master-authorized-networks 203.0.113.0/24
```

## Workload Identity Federation for GKE

Replaces node-wide service-account keys. Enabled by default on Autopilot; on Standard needs `--workload-pool` on the cluster and `GKE_METADATA` on node pools.

```bash
# Enable on existing Standard cluster + node pool
gcloud container clusters update demo-std --region us-central1 --workload-pool=PROJECT_ID.svc.id.goog
gcloud container node-pools update default-pool --cluster demo-std --region us-central1 \
  --workload-metadata=GKE_METADATA
```

Preferred (direct) IAM: grant roles straight to the Kubernetes service account principal; no GSA needed:

```bash
kubectl create namespace app
kubectl create serviceaccount app-ksa -n app
gcloud projects add-iam-policy-binding PROJECT_ID \
  --role roles/storage.objectViewer \
  --member "principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/app/sa/app-ksa"
```

Legacy GSA impersonation (needed for APIs not supporting direct principals):

```bash
gcloud iam service-accounts add-iam-policy-binding gsa@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[app/app-ksa]"
kubectl annotate serviceaccount app-ksa -n app \
  iam.gke.io/gcp-service-account=gsa@PROJECT_ID.iam.gserviceaccount.com
```

Verify from a pod: `kubectl run -it --rm wi-test -n app --image=google/cloud-sdk:slim --overrides='{"spec":{"serviceAccountName":"app-ksa"}}' -- gcloud auth list` **(unverified)**.

## Release channels and upgrades

- Channels: `rapid`, `regular` (default choice), `stable`, `extended` (longer support, extra cost in extended period). Use `regular` for prod, `rapid` for dev.
- Do not use "static" no-channel versions for new clusters.
- Control upgrade timing with maintenance windows and exclusions, not by avoiding the channel.

```bash
gcloud container clusters update demo-std --region us-central1 \
  --maintenance-window-start 2026-01-01T04:00:00Z \
  --maintenance-window-end 2026-01-01T12:00:00Z \
  --maintenance-window-recurrence "FREQ=WEEKLY;BYDAY=SA,SU"
gcloud container clusters describe demo-std --region us-central1 \
  --format="value(releaseChannel.channel,currentMasterVersion)"
```

## Node pools (Standard)

```bash
gcloud container node-pools create spot-pool --cluster demo-std --region us-central1 \
  --machine-type e2-standard-4 --spot \
  --enable-autoscaling --min-nodes 0 --max-nodes 5 \
  --node-taints dedicated=batch:NoSchedule --node-labels workload=batch \
  --workload-metadata=GKE_METADATA --shielded-secure-boot
gcloud container node-pools list --cluster demo-std --region us-central1
```

- In regional clusters `--num-nodes`/`--min/max-nodes` are **per zone**.
- Auto-upgrade and auto-repair stay on; tune surge: `--max-surge-upgrade 1 --max-unavailable-upgrade 0`.
- Use a dedicated least-privilege node service account, never the default Compute SA with Editor.
- Pods use tolerations + nodeSelector to land on tainted pools.

## Network policy

Two options (pick one): **Dataplane V2** (Cilium/eBPF, enforcement built in, set at cluster creation; default on Autopilot) or Calico (`--enable-network-policy`). Policies are no-ops without enforcement.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny, namespace: app}
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: allow-dns-and-web, namespace: app}
spec:
  podSelector: {matchLabels: {app: web}}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: kube-system}}
    ports: [{protocol: UDP, port: 53}, {protocol: TCP, port: 53}]
```

Always allow DNS egress after a default-deny egress policy.

## Binary Authorization basics

Admission control that only lets signed/attested images deploy.

```bash
gcloud services enable binaryauthorization.googleapis.com containeranalysis.googleapis.com
gcloud container clusters update demo-std --region us-central1 \
  --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE
gcloud container binauthz policy export > policy.yaml   # edit, then:
gcloud container binauthz policy import policy.yaml
```

Minimal policy: default rule `REQUIRE_ATTESTATION` with `ENFORCED_BLOCK_AND_AUDIT_LOG` and an attestor; allowlist system images via `admissionWhitelistPatterns`. Start with `DRYRUN_AUDIT_LOG_ONLY`, review Cloud Audit Logs, then enforce. Break-glass: pod annotation `alpha.image-policy.k8s.io/break-glass: "true"` (audited).

## Terraform (google provider)

Full validated example: `references/main.tf`. Key shape:

```hcl
resource "google_container_cluster" "std" {
  name                     = "demo-std"
  location                 = "us-central1"
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = true
  release_channel { channel = "REGULAR" }
  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
  datapath_provider = "ADVANCED_DATAPATH" # Dataplane V2
}
```

Autopilot: `enable_autopilot = true` (omit node pools / `remove_default_node_pool`). Manage node pools as separate `google_container_node_pool` resources.

## Pitfalls

- Private nodes without Cloud NAT/Private Google Access: pods stuck `ImagePullBackOff` on non-GCR registries.
- Authorized networks omitted/wrong: `kubectl` times out; add your current egress IP (`curl ifconfig.me`).
- `--enable-network-policy` and Dataplane V2 together are invalid.
- Workload Identity on Standard: forgetting `GKE_METADATA` on existing node pools means pods still use the node SA.
- Terraform: default `deletion_protection = true` blocks `destroy`; inline `node_pool` plus separate node pool resources conflicts and recreates the cluster.
- Terraform `location` as a zone gives a zonal cluster (single control plane); use a region for HA.
- Changing private-cluster/Dataplane/Autopilot settings often forces cluster replacement; read `terraform plan` for `must be replaced`.
- Regional node counts are per zone, so costs triple versus expectation.
- Binary Authorization enforced before attestor/allowlist is set blocks system pods; always dry-run first.
- Autopilot pods without resource requests get defaults and are billed on them.

## Verification

```bash
gcloud container clusters describe NAME --region REGION \
  --format="yaml(privateClusterConfig,workloadIdentityConfig,releaseChannel,networkConfig.datapathProvider,binaryAuthorization)"
kubectl get nodes -o wide
kubectl auth can-i --list -n app --as=system:serviceaccount:app:app-ksa
terraform fmt -check && terraform validate
```
