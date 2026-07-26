# Argo Workflows CLI and Operations Reference

This note distills the official Argo Workflows walkthroughs into an operator-focused quick reference for submitting, inspecting, and cleaning up workflows.

## Source Basis

Derived from:
- Argo Workflows docs: `https://argo-workflows.readthedocs.io/en/latest/`
- Walk-through docs, especially hello-world and argo-cli
- Official examples repo under `argoproj/argo-workflows/examples`

## Core operating flow

Use this sequence when validating a cluster, a namespace, or a new workflow spec:

```bash
# submit from a local manifest and watch until completion
argo submit --watch workflow.yaml

# submit from a URL (useful for smoke tests)
argo submit -n argo --watch \
  https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml

# inspect workflow status and node tree
argo get <workflow-name>

# tail logs from all nodes
argo logs <workflow-name>

# list recent workflows
argo list

# delete a finished or obsolete workflow
argo delete <workflow-name>
```

If the cluster uses a non-default namespace, pass `-n <namespace>` consistently to `argo` and `kubectl` commands.

## Connectivity checks

A common local access pattern is port-forwarding the Argo server:

```bash
kubectl -n argo port-forward service/argo-server 2746:2746
```

Use this when:
- testing CLI connectivity from a workstation
- validating a new auth token or local config
- using Hera against a local port-forwarded server

## Fast smoke test

For basic installation/CRD validation, start with a minimal hello-world workflow before debugging a complex DAG:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
spec:
  entrypoint: hello-world
  templates:
    - name: hello-world
      container:
        image: busybox
        command: [echo]
        args: ["hello world"]
```

If this minimal workflow fails, debug platform prerequisites first:
- workflow CRDs installed
- controller running
- namespace correct
- service account/RBAC sufficient
- cluster can pull the referenced image

## Operational debugging checklist

### Submission fails immediately
Check:
- wrong namespace
- CLI not authenticated to the server
- CRDs missing
- server unreachable
- manifest schema errors

### Workflow object exists, but pods do not run
Check:
- entrypoint points to a real template
- template names are spelled correctly
- resource requests are schedulable
- image pull access is valid
- workflow service account has the right permissions

### Workflow runs, but behavior is wrong
Check:
- `steps` grouping vs intended parallelism
- DAG `dependencies`
- parameter interpolation paths
- artifact handoff paths and repository config
- retry and fail-fast behavior

## Suggested operator habits

1. Submit the simplest reproducible workflow first.
2. Keep the namespace explicit in every command.
3. Use `argo get` and `argo logs` before changing the manifest.
4. Prefer a local file during iteration; use remote example URLs only for smoke tests.
5. Delete old test workflows so list/get output stays readable.

## Related skill routing

- Use `argocd` for GitOps app reconciliation and sync operations.
- Use `argocd-advanced` for ApplicationSet, image updater, and cluster bootstrapping.
- Use `python-dev` together with this skill when Hera code needs broader Python project work.
