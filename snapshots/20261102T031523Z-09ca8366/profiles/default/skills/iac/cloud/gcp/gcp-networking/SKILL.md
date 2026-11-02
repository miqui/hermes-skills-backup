---
name: gcp-networking
description: Use when designing, deploying, or debugging Google Cloud networking. Covers custom-mode VPC subnets, Private Google Access, Cloud NAT, firewall rules (tags/service accounts), Private Service Connect, Cloud DNS, and Shared VPC basics, with gcloud and Terraform examples.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gcp, networking, vpc, terraform, gcloud, cloud-nat, dns, psc]
    related_skills: [terraform-infrastructure, cloud-architect]
---

# GCP Networking

Terraform (google provider) example: `examples/terraform/main.tf` (passes `terraform fmt -check` and `terraform validate`, v1.16.2, `init -backend=false`; never applied). gcloud commands below are **unverified against a live project**; check `gcloud compute <cmd> --help` for your SDK version.

## Rules of thumb
- VPCs are global, subnets are regional, firewall rules and routes are global per VPC. Use **custom mode** (`--subnet-mode=custom` / `auto_create_subnetworks=false`); auto mode's /20 per region overlaps with peering/VPN ranges and can't be converted back.
- Plan CIDRs up front (non-overlapping with on-prem and peered VPCs). A subnet's primary range can be expanded, never shrunk.
- Prefer no external IPs: Private Google Access + Cloud NAT + IAP for SSH.

## VPC and subnets
```bash
gcloud compute networks create app-vpc --subnet-mode=custom --bgp-routing-mode=regional
gcloud compute networks subnets create app-us-central1 \
  --network=app-vpc --region=us-central1 --range=10.10.0.0/24 \
  --enable-private-ip-google-access --enable-flow-logs
gcloud compute networks subnets expand-ip-range app-us-central1 --region=us-central1 --prefix-length=23
```

## Private Google Access (PGA)
Per-subnet flag letting VMs with only internal IPs reach Google APIs (default `*.googleapis.com` names, or `private.googleapis.com` 199.36.153.8/30 / `restricted.googleapis.com` 199.36.153.4/30 for VPC-SC). A route to the API VIPs (default internet gateway next hop) must exist.
```bash
gcloud compute networks subnets update app-us-central1 --region=us-central1 --enable-private-ip-google-access
```

## Cloud NAT
Regional, attached to a Cloud Router; outbound only, for VMs without external IPs (including GKE nodes).
```bash
gcloud compute routers create app-router --network=app-vpc --region=us-central1
gcloud compute routers nats create app-nat --router=app-router --region=us-central1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges --enable-logging
```
For predictable egress IPs use reserved addresses (`--nat-external-ip-pool=`). Raise `--min-ports-per-vm` or enable dynamic port allocation if logs show `OUT_OF_RESOURCES` / dropped connections.

## Firewall rules
- Implied: deny all ingress, allow all egress (priority 65535). Lower number = higher priority; deny wins on ties.
- Stateful. Target by **network tags** (easy, but anyone who can edit instances can set them) or **service accounts** (IAM-controlled, preferred for tier isolation). **Tags and service accounts can't be mixed in one rule.**
```bash
gcloud compute firewall-rules create allow-iap-ssh --network=app-vpc --direction=INGRESS \
  --allow=tcp:22 --source-ranges=35.235.240.0/20 --target-tags=ssh-iap
gcloud compute firewall-rules create allow-web-to-db --network=app-vpc --direction=INGRESS \
  --allow=tcp:5432 --source-service-accounts=web-tier-sa@PROJECT.iam.gserviceaccount.com \
  --target-service-accounts=db-tier-sa@PROJECT.iam.gserviceaccount.com
gcloud compute firewall-rules list --filter="network:app-vpc" --sort-by=priority
```
Load balancer health-check ranges (130.211.0.0/22, 35.191.0.0/16) must be allowed. For org-wide policy use hierarchical / network firewall policies.

## Private Service Connect (PSC)
- **To Google APIs:** internal global IP + global forwarding rule targeting `all-apis` (or `vpc-sc`). Rule name: lowercase letters/digits, ≤20 chars.
- **To published services:** regional forwarding rule targeting the producer's service attachment; producer side needs a NAT subnet with `--purpose=PRIVATE_SERVICE_CONNECT` and must accept your project.
```bash
gcloud compute addresses create psc-apis-ip --global --purpose=PRIVATE_SERVICE_CONNECT \
  --addresses=10.10.255.1 --network=app-vpc
gcloud compute forwarding-rules create pscapis --global --network=app-vpc \
  --address=psc-apis-ip --target-google-apis-bundle=all-apis
# published service (psc-svc-ip: a regional internal address you reserved)
gcloud compute forwarding-rules create psc-to-svc --region=us-central1 --network=app-vpc \
  --subnet=app-us-central1 --address=psc-svc-ip \
  --target-service-attachment=projects/PRODUCER/regions/us-central1/serviceAttachments/NAME
```
Pair the API endpoint with private DNS so clients resolve to it (Google's docs use `p.googleapis.com` names, or a `googleapis.com` zone pointing at the endpoint IP).

## Cloud DNS
Private zones resolve only from attached VPCs. Also: forwarding zones (to on-prem), peering zones (resolve via another VPC), inbound server policies (on-prem → GCP).
```bash
gcloud dns managed-zones create corp-internal --dns-name=corp.internal. \
  --visibility=private --networks=app-vpc --description="internal"
gcloud dns record-sets create db.corp.internal. --zone=corp-internal --type=A --ttl=300 --rrdatas=10.10.0.10
```
Names need the trailing dot.

## Shared VPC basics
Host project owns the network; service projects attach VMs/GKE to it. Enabling requires `roles/compute.xpnAdmin` at org or folder.
```bash
gcloud compute shared-vpc enable HOST_PROJECT
gcloud compute shared-vpc associated-projects add SERVICE_PROJECT --host-project=HOST_PROJECT
gcloud compute networks subnets add-iam-policy-binding app-us-central1 --region=us-central1 \
  --project=HOST_PROJECT --member="group:app-team@example.com" --role=roles/compute.networkUser
```
Grant `networkUser` per subnet (least privilege). GKE in a service project also needs the GKE service agent to have `roles/container.hostServiceAgentUser` on the host project and `networkUser` on the subnet.

## Workflow
1. Plan CIDRs; custom VPC + subnets (PGA on).
2. Router + NAT; IAP for admin access.
3. Firewall rules by service account/tag, least privilege.
4. DNS zones; PSC endpoints for private API/service access.
5. Shared VPC if multiple projects share the network.
6. `terraform fmt -check && terraform validate`, then `plan` in a sandbox project before apply.

## Pitfalls
- The auto-mode `default` network in new projects: delete it or avoid it.
- Subnets can't shrink or overlap peered/VPN ranges; VPC peering is non-transitive.
- Cloud NAT gives no ingress and doesn't apply to VMs with external IPs.
- PGA ≠ PSC. PGA doesn't reach the general internet; a PSC endpoint is unused unless DNS points at it.
- Terraform `account_id` for service accounts must be 6–30 chars (caught by `validate`).
- Renaming a firewall rule is destroy+create and can briefly drop traffic; use `create_before_destroy` with new names.
- Shared VPC attach/detach is org-level IAM; Terraform must run with credentials that have it.
- If you add a deny-all egress rule, explicitly allow Google API/PSC IPs, DNS, IAP and health checks.
- Never commit `*.tfstate`, `.terraform/` or credentials.
