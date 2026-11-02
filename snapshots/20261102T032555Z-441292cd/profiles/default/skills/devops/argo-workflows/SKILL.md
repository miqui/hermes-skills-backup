---
name: argo-workflows
description: Use when building, submitting, or troubleshooting Argo Workflows on Kubernetes, including Workflow/CronWorkflow specs, steps vs DAG patterns, artifacts and parameters, Argo CLI operations, and Hera Python SDK authoring.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [argo-workflows, hera, kubernetes, workflows, dag, cronworkflow, ci-cd]
    related_skills: [argocd, argocd-advanced, deployment-engineer, python-dev]
---

# Argo Workflows

## Overview

Use this skill when the task is about the **workflow engine** in the Argo ecosystem: defining `Workflow` or `CronWorkflow` specs, choosing between `steps` and `dag`, passing parameters or artifacts between tasks, submitting/rerunning workflows with the Argo CLI, or authoring workflows in Python with the Hera SDK.

This skill belongs under `devops`, not `software-development` or `iac`, because its center of gravity is Kubernetes-native workflow orchestration, CI/CD and batch execution, and platform operations. Hera is part of this skill as the Python authoring interface for Argo Workflows, not a separate taxonomy root.

Use `argocd` for GitOps application reconciliation and environment sync. Use `argocd-advanced` for ApplicationSet, image updater, and cluster bootstrapping.

## When to Use

- Authoring or reviewing Argo `Workflow`, `WorkflowTemplate`, `ClusterWorkflowTemplate`, or `CronWorkflow` manifests
- Choosing between step-based execution and DAG-based execution
- Running workflows with the Argo CLI and inspecting status, logs, or failures
- Designing batch, ML, infrastructure automation, or CI pipelines that execute on Kubernetes
- Writing Argo Workflows in Python using Hera
- Troubleshooting workflow submission, scheduling, retries, artifacts, parameters, or execution order

Do not use this skill for:
- Argo CD `Application`, `ApplicationSet`, repo, cluster, or sync operations
- General Python project work that is not specifically about Hera or Argo Workflows
- Terraform/CloudFormation style infrastructure provisioning as the primary task

## Core Mental Model

Argo Workflows is a Kubernetes-native workflow engine implemented with CRDs.
Each workflow step is typically a container execution. The main design choice is how you model dependencies:

- **steps**: ordered phases, with optional parallelism inside each phase
- **dag**: explicit dependency graph for more flexible orchestration

Reach for:
- `Workflow` for one-off runs
- `CronWorkflow` for scheduled runs
- `WorkflowTemplate` / `ClusterWorkflowTemplate` for reusable building blocks
- **Hera** when Python is the preferred authoring surface

## Taxonomy Placement

### Why `devops`

This skill fits `devops` because it is primarily about:
- Kubernetes execution orchestration
- CI/CD and automation pipelines
- batch/data/ML job coordination
- operational workflow submission, retry, and observability

### Why not `software-development`

Although Hera is Python-based, the problem domain is not general application coding; it is orchestrating execution on Kubernetes.

### Why not `iac`

Workflows may provision or operate infrastructure, but the main object of work is the workflow runtime and spec model, not cloud resource modeling.

## Quick Reference

| Need | Use |
|---|---|
| Submit a one-off workflow manifest | `argo submit --watch workflow.yaml` |
| Inspect workflow status | `argo get <name>` |
| Tail workflow logs | `argo logs <name>` |
| Schedule recurring runs | `CronWorkflow` |
| Linear phases with occasional parallel fan-out | `steps` |
| Rich dependency graph | `dag` |
| Python authoring | Hera |

## Supporting References

- `references/cli-and-operations.md` — operator-focused CLI flow, connectivity checks, smoke tests, and debugging sequence
- `references/authoring-patterns.md` — when to choose `Workflow` vs `CronWorkflow`, `steps` vs `dag`, and parameters vs artifacts
- `references/hera-quickstart.md` — Hera-specific setup, minimal example, and Python authoring guidance

## Authoring Patterns

### Hello world workflow

The Argo docs' basic pattern is a `Workflow` with an `entrypoint` and one or more templates:

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
        resources:
          limits:
            memory: 32Mi
            cpu: 100m
```

Use this as the minimal baseline when verifying cluster installation, CLI connectivity, or CRD health.

### Steps pattern

Use `steps` when the workflow is naturally organized into phases.
The walkthrough shows the important semantic difference:
- separate step groups run sequentially
- items within the same group can run in parallel

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: steps-
spec:
  entrypoint: hello-hello-hello
  templates:
  - name: hello-hello-hello
    steps:
    - - name: hello1
        template: print-message
        arguments:
          parameters:
          - name: message
            value: "hello1"
    - - name: hello2a
        template: print-message
        arguments:
          parameters:
          - name: message
            value: "hello2a"
      - name: hello2b
        template: print-message
        arguments:
          parameters:
          - name: message
            value: "hello2b"
  - name: print-message
    inputs:
      parameters:
      - name: message
    container:
      image: busybox
      command: [echo]
      args: ["{{inputs.parameters.message}}"]
```

Choose `steps` first when the sequence is easy to read top-to-bottom and complex branching is unnecessary.

### DAG pattern

Use `dag` when you need explicit dependency modeling.
The Argo walkthrough's diamond example is the canonical mental model:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: dag-diamond-
spec:
  entrypoint: diamond
  templates:
  - name: echo
    inputs:
      parameters:
      - name: message
    container:
      image: alpine:3.23
      command: [echo, "{{inputs.parameters.message}}"]
  - name: diamond
    dag:
      tasks:
      - name: A
        template: echo
        arguments:
          parameters: [{name: message, value: A}]
      - name: B
        dependencies: [A]
        template: echo
        arguments:
          parameters: [{name: message, value: B}]
      - name: C
        dependencies: [A]
        template: echo
        arguments:
          parameters: [{name: message, value: C}]
      - name: D
        dependencies: [B, C]
        template: echo
        arguments:
          parameters: [{name: message, value: D}]
```

Use DAGs when dependency clarity matters more than sequential readability.

## Argo CLI Workflow

### Install and connectivity

The official walkthrough uses patterns like:

```bash
argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml
kubectl -n argo port-forward service/argo-server 2746:2746
```

Practical operating flow:

```bash
# submit from file and wait
argo submit --watch workflow.yaml

# inspect a workflow
argo get <workflow-name>

# view logs
argo logs <workflow-name>

# list workflows
argo list

# delete old workflows
argo delete <workflow-name>
```

If the environment uses namespaces heavily, include `-n <namespace>` consistently.

## CronWorkflows

Use `CronWorkflow` when the workload should run on a schedule rather than by manual submission.

Typical pattern:
- keep the workflow body small and delegate to reusable templates where possible
- ensure jobs are idempotent or concurrency-safe
- define history retention and concurrency behavior intentionally

Skeleton:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: nightly-maintenance
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: "Forbid"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  workflowSpec:
    entrypoint: run-job
    templates:
      - name: run-job
        container:
          image: alpine:3.23
          command: [sh, -c]
          args: ["echo running nightly maintenance"]
```

## Parameters and Artifacts

Use:
- **parameters** for small structured values, flags, names, and runtime inputs
- **artifacts** for files, reports, archives, model outputs, or other larger payloads

As a rule of thumb:
- if another task only needs a string or scalar, pass a parameter
- if it needs a file or directory payload, use artifacts

When troubleshooting handoff failures, inspect:
- template input/output names
- parameter interpolation syntax
- artifact repository configuration
- path mismatches between producer and consumer steps

## Retry, Failure, and Control Flow

Common control mechanisms to model explicitly:
- retries for flaky remote calls or transient Kubernetes issues
- timeouts for runaway jobs
- exit handlers for cleanup or notifications
- suspend points for approval gates or manual intervention
- conditionals for branching behavior

For DAGs specifically, remember the documented default: **fail fast**. When one task fails, no new tasks are scheduled unless the workflow is modeled otherwise.

## Hera Python SDK

Hera is the Python SDK for Argo Workflows and should be treated as the Python-native authoring path inside this skill.

The quick-start docs show:
- install with `pip install hera`
- local port-forward to the Argo server
- author a workflow in Python and submit it with `w.create()`

Representative pattern:

```python
from hera.workflows import Steps, Workflow, WorkflowsService, script

@script()
def echo(message: str):
    print(message)

with Workflow(
    generate_name="hello-world-",
    entrypoint="steps",
    namespace="argo",
    workflows_service=WorkflowsService(host="https://localhost:2746"),
) as w:
    with Steps(name="steps"):
        echo(arguments={"message": "Hello world!"})

submitted_workflow = w.create()
print(submitted_workflow.metadata.name)
```

Use Hera when:
- workflow specs benefit from Python composition or reuse
- the team prefers code generation over hand-authored YAML
- you need tighter integration with Python-based tooling or libraries

Prefer plain YAML when:
- the workflow should stay maximally transparent to ops teams
- Git review readability matters more than code abstraction
- no Python-specific abstraction benefit is needed

## Troubleshooting Flow

### Submission failures

Check:
- CRDs are installed
- namespace is correct
- Argo server is reachable or `--server`/auth is correct
- service account and RBAC are sufficient

### Workflow starts but tasks do not run

Check:
- `entrypoint` matches a real template
- template names are spelled correctly
- images are pullable from the cluster
- node scheduling/resource limits are not blocking pods

### DAG/steps behavior is wrong

Check:
- `steps` nesting and dash structure for parallel vs sequential behavior
- `dependencies` in DAG tasks
- fail-fast semantics and retry policy
- parameter interpolation paths like `{{inputs.parameters.foo}}`

### Hera-specific issues

Check:
- Argo server connectivity and port-forward
- auth token or host configuration
- generated workflow content if Python abstraction obscures the actual manifest
- that the runtime image used by `@script()` is available to the cluster

## Common Pitfalls

1. **Confusing Argo Workflows with Argo CD.**
   Argo CD reconciles desired application state from Git. Argo Workflows executes task graphs.

2. **Using `dag` when `steps` would be clearer.**
   Reach for the simpler model first.

3. **Modeling file handoff as parameters.**
   Use artifacts for file payloads.

4. **Forgetting namespace context.**
   `argo submit`, `argo get`, and `kubectl` checks often fail simply because the wrong namespace is in use.

5. **Letting Hera hide the actual workflow semantics.**
   If debugging gets confusing, inspect the rendered workflow shape and compare it to the YAML mental model.

6. **Treating scheduled workflows as stateless when they are not.**
   Cron jobs must be idempotent or concurrency-controlled.

7. **Ignoring DAG fail-fast behavior.**
   One failed task can stop additional scheduling even while other running tasks finish.

## Verification Checklist

- [ ] The task is truly about Argo Workflows rather than Argo CD
- [ ] `Workflow` vs `CronWorkflow` vs template reuse was chosen deliberately
- [ ] `steps` vs `dag` was chosen for clarity and dependency shape
- [ ] Parameters vs artifacts were separated correctly
- [ ] Namespace, auth, and submission path were verified
- [ ] If using Hera, the generated workflow intent still matches the Kubernetes execution model
- [ ] The skill routes related Argo CD concerns to `argocd` or `argocd-advanced`
