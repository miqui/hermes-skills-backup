---
name: kubernetes
description: Use when working on general Kubernetes cluster and workload operations, including kubectl inspection, manifests, Deployments/Services/Ingress, ConfigMaps/Secrets, probes, Jobs/CronJobs, Helm/Kustomize-aware troubleshooting, RBAC (Role/ClusterRole/RoleBinding/ServiceAccount), and routine pod/scheduling/network diagnosis.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kubernetes, k8s, kubectl, helm, kustomize, deployment, ingress, debugging, devops, rbac, security, serviceaccount]
    related_skills: [argocd, argo-workflows, deployment-engineer, crossplane, cloud-architect, ai-generated-iac-governance]
---

# Kubernetes

## Overview

Use this skill for **general-purpose Kubernetes work** when the task is about inspecting, authoring, operating, or troubleshooting workloads and cluster resources in a standard Kubernetes environment.

This is the primary routing point for day-to-day Kubernetes operations: identifying the correct cluster and namespace, reading resource state with `kubectl`, understanding how objects relate to one another, diagnosing rollout failures, checking events and pod conditions, and making safe manifest-level changes.

This skill is intentionally **generic and platform-neutral**. It should help whether the cluster is self-managed or hosted on EKS, GKE, AKS, k3s, or another conformant Kubernetes distribution. If the task becomes provider-specific, load the cloud-specific skill as a companion rather than overloading this one.

## When to Use

Use this skill when you need to:

- Inspect or troubleshoot Kubernetes resources with `kubectl`
- Work with namespaces, contexts, labels, selectors, and annotations
- Diagnose `Deployment`, `StatefulSet`, `DaemonSet`, `Pod`, `Service`, `Ingress`, `Job`, or `CronJob` behavior
- Review or edit manifests for ConfigMaps, Secrets, probes, requests/limits, affinities, tolerations, and autoscaling inputs
- Investigate rollout failures, CrashLoopBackOff, ImagePullBackOff, Pending pods, or failing readiness/liveness probes
- Understand how application traffic reaches workloads through Services and Ingress
- Perform Helm- or Kustomize-aware troubleshooting at the rendered-manifest / runtime-resource layer
- Gather the minimum evidence needed before escalating to cloud, networking, storage, or GitOps-specific workflows
- Author, audit, or troubleshoot Kubernetes RBAC: Roles, ClusterRoles, RoleBindings, ClusterRoleBindings, and ServiceAccount least-privilege configuration

Do not use this skill for:

- Argo CD `Application` / `ApplicationSet` operations when `argocd` or `argocd-advanced` is the real center of gravity
- Argo Workflows DAG/CronWorkflow authoring when `argo-workflows` is the better fit
- Crossplane XRD/composition/provider design when `crossplane` is the better fit
- Cloud-provider-specific cluster creation or managed-service configuration as the main task
- Application feature development that happens to deploy to Kubernetes but does not require Kubernetes reasoning

## Core Mental Model

Kubernetes troubleshooting is easier when you reason in layers:

```text
Context/cluster -> namespace -> workload controller -> pods -> container state
                -> service discovery / traffic path -> storage / config / secrets
                -> node scheduling / quotas / policies -> events and logs
```

Most failures are not mysterious if you walk the stack in order:
1. Confirm the **right cluster and namespace**
2. Identify the **owning resource** (`Deployment`, `Job`, etc.)
3. Inspect the **resulting Pods**
4. Read **events**, **conditions**, and **container status**
5. Check the **traffic/config/dependency layer**
6. Only then mutate something

## First Checks Before Any Change

Always gather these before proposing a fix:

```bash
kubectl config current-context
kubectl get ns
kubectl get deploy,sts,ds,po,svc,ing -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

If the scope is unclear, identify:
- cluster/context
- namespace
- workload name
- recent change (image, config, chart release, rollout, policy)
- symptom class (not starting, not ready, not reachable, restarting, unscheduled, timing out)

## Common Operational Workflows

### 1) Inspect a workload safely

```bash
kubectl get deployment <name> -n <namespace> -o wide
kubectl describe deployment <name> -n <namespace>
kubectl get pods -n <namespace> -l app=<label>
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
```

Use this path first for:
- rollout stuck
- probe failures
- unexpected restarts
- image pull failures
- config not applied

### 2) Follow a rollout

```bash
kubectl rollout status deployment/<name> -n <namespace>
kubectl rollout history deployment/<name> -n <namespace>
kubectl describe rs -n <namespace>
```

Check:
- desired vs available replicas
- old ReplicaSets still serving
- probe failures blocking readiness
- image tag mismatch
- admission/policy rejection

### 3) Debug a Pending pod

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get nodes
kubectl top nodes
```

Typical causes:
- insufficient CPU or memory
- node selectors / affinity too restrictive
- missing toleration for tainted nodes
- PVC not bound
- quota / LimitRange / policy denial

### 4) Debug CrashLoopBackOff or restart storms

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
kubectl logs <pod-name> -n <namespace> --all-containers=true
```

Look for:
- app process exiting on startup
- bad config/env/secret values
- probe path/port mismatch
- OOMKilled
- dependency connection failure
- migration/init step failure

### 5) Debug Service or Ingress reachability

Check the traffic chain in order:

```text
Pod listens correctly?
-> Service selector matches pods?
-> Service port targets correct containerPort?
-> Endpoints / EndpointSlices populated?
-> Ingress routes to the right Service/port?
-> Controller / LB / DNS layer healthy?
```

Useful commands:

```bash
kubectl get svc <name> -n <namespace> -o yaml
kubectl get endpoints,endpointslices -n <namespace>
kubectl get ingress <name> -n <namespace> -o yaml
kubectl describe ingress <name> -n <namespace>
```

### 6) Inspect config and secret wiring

```bash
kubectl get configmap <name> -n <namespace> -o yaml
kubectl get secret <name> -n <namespace> -o yaml
kubectl describe pod <pod-name> -n <namespace>
```

Verify:
- referenced object exists in the same namespace
- key names match what the pod expects
- envFrom / volume mounts point at the intended object
- rollout occurred after config change if restart is required

### 7) Jobs and CronJobs

```bash
kubectl get jobs,cronjobs -n <namespace>
kubectl describe job <name> -n <namespace>
kubectl describe cronjob <name> -n <namespace>
kubectl logs job/<name> -n <namespace>
```

Check:
- schedule and concurrency policy
- missed schedules
- backoffLimit / restart policy
- history retention
- whether the Job-created Pod actually ran

### 8) Debug PVC and storage issues

```bash
kubectl get pvc,pv -n <namespace>
kubectl describe pvc <name> -n <namespace>
kubectl get storageclass
kubectl describe pod <pod-name> -n <namespace>
```

Check:
- whether the PVC is `Pending` or `Bound`
- storageClass name matches what the workload expects
- requested size and access mode are actually satisfiable
- dynamic provisioner exists and is healthy
- mount errors or attach failures appear in Pod events
- zone / node affinity constraints conflict with the bound volume

## Kubernetes RBAC — Safe Authoring and Auditing

### Core Concepts

Kubernetes RBAC controls what API operations a subject (user, group, or ServiceAccount) can perform on which resources.

| Object | Scope | Purpose |
| --- | --- | --- |
| `Role` | Namespace | Grants permissions within one namespace only |
| `ClusterRole` | Cluster-wide | Grants permissions across all namespaces or non-namespaced resources |
| `RoleBinding` | Namespace | Binds a Role **or** ClusterRole to subjects within one namespace |
| `ClusterRoleBinding` | Cluster-wide | Binds a ClusterRole to subjects cluster-wide |

**Decision rule:**
- Grant namespace-scoped access → use a `Role` + `RoleBinding` in that namespace.
- Reuse the same permission set across many namespaces → define one `ClusterRole`, bind it with per-namespace `RoleBindings` (not a `ClusterRoleBinding`).
- Truly cluster-wide access (e.g., `nodes`, `namespaces`, `persistentvolumes`) → only then use a `ClusterRoleBinding`, and treat it as a high-risk grant.

### ServiceAccount Least Privilege

- Every Pod runs as a ServiceAccount. When not specified it defaults to the `default` ServiceAccount in the namespace, which inherits whatever is bound to it — this is often more than needed.
- Create a dedicated ServiceAccount per workload with only the permissions that workload actually requires.
- Opt-out of auto-mounting the API token when the workload does not need API access:
  ```yaml
  automountServiceAccountToken: false
  ```
- Namespace default ServiceAccounts should carry **no bindings** beyond Kubernetes defaults.

### `resourceNames` Cautions

`resourceNames` narrows a rule to specific named instances of a resource. Use it when the scope is truly known and static. Avoid it as a substitute for proper namespace separation, and note that it does **not** apply to `create` (the resource does not exist yet at create time).

### Safe RBAC Authoring Examples

#### Minimal Role + RoleBinding (read-only pods in one namespace)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: my-app
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: my-app
subjects:
  - kind: ServiceAccount
    name: my-app-sa
    namespace: my-app
roleRef:
  kind: Role
  apiGroup: rbac.authorization.k8s.io
  name: pod-reader
```

#### Dedicated ServiceAccount with token opt-out

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: my-app
automountServiceAccountToken: false
```

**Do not use wildcard `*` for verbs or resources.** Enumerate only what is needed; wildcards bypass the audit trail and mask future over-permissioning.

### Inspection and Audit Commands

```bash
# List all Roles and ClusterRoles
kubectl get roles -n <namespace>
kubectl get clusterroles | grep -v system:

# List bindings
kubectl get rolebindings -n <namespace>
kubectl get clusterrolebindings

# Show full details of a Role
kubectl describe role <name> -n <namespace>
kubectl describe clusterrole <name>

# Show who is bound to a ClusterRole
kubectl get clusterrolebindings -o json \
  | jq '.items[] | select(.roleRef.name=="<name>") | {name:.metadata.name, subjects:.subjects}'

# Show all bindings for a ServiceAccount
kubectl get rolebindings,clusterrolebindings -A \
  -o custom-columns='KIND:.kind,NAME:.metadata.name,NAMESPACE:.metadata.namespace,SUBJECT:.subjects[*].name' \
  | grep <sa-name>
```

### Permission Testing with `kubectl auth can-i`

```bash
# Can the current user list pods in namespace?
kubectl auth can-i list pods -n <namespace>

# Impersonate a ServiceAccount to test its permissions
kubectl auth can-i list pods -n <namespace> \
  --as=system:serviceaccount:<namespace>:<sa-name>

# Enumerate all permissions for a ServiceAccount in a namespace
kubectl auth can-i --list -n <namespace> \
  --as=system:serviceaccount:<namespace>:<sa-name>
```

Always test using impersonation **before** deploying a workload that depends on specific permissions — it avoids runtime surprises.

### Troubleshooting Permission-Denied Errors

When a workload gets a `403 Forbidden` from the Kubernetes API:

1. Identify the **ServiceAccount** the Pod is running as:
   ```bash
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'
   ```
2. Determine the exact API call that failed (check app logs for `verb`, `resource`, `apiGroup`).
3. Test with impersonation:
   ```bash
   kubectl auth can-i <verb> <resource> -n <namespace> \
     --as=system:serviceaccount:<namespace>:<sa-name>
   ```
4. If it returns `no`, inspect bindings on that ServiceAccount and create/update the Role + RoleBinding.
5. If it returns `yes` but the app still fails, check for admission webhooks, NetworkPolicy blocking API server egress, or token mount issues.

### RBAC vs NetworkPolicy

These are distinct controls — do not conflate them:

| | RBAC | NetworkPolicy |
| --- | --- | --- |
| Controls | API-server authorization | Pod-to-pod / pod-to-external network traffic |
| Subjects | Users, groups, ServiceAccounts | Pod label selectors, namespace selectors, IP blocks |
| Enforced by | kube-apiserver | CNI plugin (Calico, Cilium, etc.) |
| Default posture | All API access denied unless a binding grants it | All traffic allowed unless a policy restricts it |

A Pod with no RBAC binding cannot call the Kubernetes API. A Pod with no NetworkPolicy is still reachable on the network (unless the CNI enforces a default-deny).

### GitOps / Source-First Caution

When RBAC resources are managed by Argo CD, Helm, or Kustomize:
- **Do not patch live Role/RoleBinding objects directly.** Reconcilers will revert the change.
- Make RBAC changes in the source repository and let GitOps apply them — this preserves audit history.
- If emergency access is needed, create a **time-limited, narrowly-scoped** RoleBinding and immediately follow up with a source commit to reflect the intended state.
- See the `argocd` and `ai-generated-iac-governance` skills for GitOps-safe change patterns.

## Manifest Review Heuristics

When reviewing Kubernetes YAML, inspect these fields first:

| Area | What to verify |
| --- | --- |
| Metadata | correct namespace, labels, selectors, owner assumptions |
| Image | exact image/tag, pull policy, registry access |
| Probes | path/port/scheme/thresholds/startup timing |
| Resources | requests and limits are realistic |
| Scheduling | nodeSelector, affinity, tolerations, topology spread |
| Config | ConfigMaps/Secrets keys exist and are mounted correctly |
| Networking | Service selectors and target ports align with Pods |
| Storage | PVC names, access modes, storage class assumptions |
| Security | serviceAccountName, runAs settings, capabilities, policy interactions |
| RBAC | Role/ClusterRole scope correct; no wildcard verbs/resources; RoleBinding subject and namespace match; ServiceAccount is dedicated and least-privilege; token auto-mount disabled if unused |

## Helm and Kustomize Routing

Use this skill for runtime troubleshooting even when the source is Helm or Kustomize.

- **Helm concern**: rendered manifests, values wiring, release drift, resource naming
- **Kustomize concern**: overlays, patches, name prefixes/suffixes, environment-specific diffs
- **Kubernetes concern**: what actually exists in the cluster and why it behaves that way

If the problem is “the cluster objects are wrong,” inspect the live objects first. Then trace back to Helm values or Kustomize overlays.

## Safe Mutation Guidance

Prefer the narrowest viable change and verify immediately after:

- favor manifest/source updates over ad hoc imperative changes when GitOps is in play
- if you must patch live state, scope it tightly and document the intended rollback path
- avoid deleting resources unless you understand the owning controller and recreation behavior
- confirm whether the resource is managed by Helm, Argo CD, or another reconciler before changing it

Typical verification after a change:

```bash
kubectl rollout status deployment/<name> -n <namespace>
kubectl get pods -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

## Common Pitfalls

1. **Wrong context or namespace.**
   Many “missing resource” and “nothing changed” incidents are really scope mistakes. Confirm context and namespace first.

2. **Reading only logs and skipping events/describe output.**
   Kubernetes often tells you the real cause in Pod conditions or events, not just container stdout.

3. **Confusing Service success with Pod health.**
   A Service can exist while routing nowhere because selectors do not match or endpoints are empty.

4. **Changing live resources managed by GitOps or Helm without realizing it.**
   Reconciliation may revert the change or hide the true source of drift.

5. **Probe misconfiguration interpreted as app failure.**
   Wrong path, port, or startup timing can make a healthy app look broken.

6. **Ignoring resource requests and scheduling constraints.**
   Pending pods often come from unschedulable requirements, not broken images.

7. **Treating Secrets as a pure application issue.**
   Missing keys, namespace mismatch, bad mounts, and rollout timing are frequent Kubernetes-layer causes.

8. **Debugging ingress before confirming service endpoints.**
   Start close to the pod and move outward; do not begin at DNS/LB unless inner layers are already verified.

9. **Granting wildcard permissions in RBAC.**
   `verbs: ["*"]` or `resources: ["*"]` grants full control and bypasses fine-grained auditing. Always enumerate only the specific verbs and resources the workload actually uses.

10. **Binding ClusterRoles cluster-wide when namespace scope suffices.**
    A `ClusterRoleBinding` applies permissions across every namespace. Prefer a `RoleBinding` per namespace to limit blast radius.

11. **Leaving the `default` ServiceAccount unguarded.**
    Workloads that do not specify a ServiceAccount run as `default`. Ensure no broad bindings are attached to namespace default ServiceAccounts.

12. **Patching live RBAC objects when GitOps owns them.**
    Argo CD or Helm will reconcile the change back. Always source-first for RBAC changes in GitOps environments.

## Verification Checklist

- [ ] Confirmed cluster context and namespace
- [ ] Identified the owning workload resource and resulting Pods
- [ ] Reviewed `describe` output and recent events before proposing a fix
- [ ] Checked logs only after understanding container state and probe behavior
- [ ] Verified Service/Ingress wiring if the symptom is reachability
- [ ] Checked config/secret references if the symptom is startup or runtime misbehavior
- [ ] Considered scheduling/resource constraints for Pending or unstable pods
- [ ] Checked PVC/PV/storage class state when symptoms suggest storage or mount issues
- [ ] Determined whether Helm, Argo CD, or another reconciler owns the resource
- [ ] Checked RBAC when symptom is `403 Forbidden` or unexpected API access: identified ServiceAccount, tested with `kubectl auth can-i --as=system:serviceaccount:<ns>:<sa>`, verified no wildcard grants
- [ ] Confirmed any new Role/RoleBinding is namespace-scoped unless cluster-wide access is genuinely required
- [ ] Chosen the narrowest safe change with an obvious verification path
- [ ] Re-checked rollout / pod health / events after mutation
