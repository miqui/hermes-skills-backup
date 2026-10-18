# Argo Workflows Authoring Patterns

This reference captures the main authoring choices from the official walkthroughs: when to use `Workflow`, `CronWorkflow`, `steps`, `dag`, parameters, artifacts, and reusable templates.

## Source Basis

Derived from:
- Argo Workflows docs: `https://argo-workflows.readthedocs.io/en/latest/`
- Walk-through pages for hello-world, steps, dag, and cron-workflows
- Official examples repo under `argoproj/argo-workflows/examples`

## Pick the right top-level resource

| Need | Prefer |
| --- | --- |
| One-off execution | `Workflow` |
| Scheduled execution | `CronWorkflow` |
| Reusable namespaced building block | `WorkflowTemplate` |
| Reusable cluster-wide building block | `ClusterWorkflowTemplate` |

## Steps vs DAG

### Use `steps` when:
- the workflow is naturally phase-based
- human readability matters most
- sequential groups with occasional parallel fan-out are enough

Key semantic rule from the walkthrough:
- step groups run sequentially
- items inside the same group can run in parallel

### Use `dag` when:
- dependency structure is the main concern
- tasks fan out and converge
- explicit edges are clearer than ordered phases

The canonical mental model is the diamond DAG:
- A runs first
- B and C depend on A
- D depends on both B and C

## Parameters vs artifacts

Use **parameters** for:
- names
- flags
- scalar values
- small structured inputs

Use **artifacts** for:
- files
- archives
- reports
- model outputs
- directory payloads passed between tasks

Rule of thumb:
- if the consumer only needs a small value, use a parameter
- if the consumer needs bytes on disk, use an artifact

## CronWorkflow guidance

Use `CronWorkflow` when a run is schedule-driven rather than manually submitted.

Design intentionally for:
- idempotency
- concurrency behavior
- history retention
- reusable embedded workflow logic

Representative skeleton:

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

## Common authoring decisions

### Start with a minimal workflow
Use a tiny hello-world workflow to verify:
- CRDs are healthy
- the namespace is correct
- the controller is scheduling pods
- the CLI path works

### Prefer the simplest graph that communicates intent
- choose `steps` first when it is enough
- move to `dag` only when the dependency graph is genuinely richer

### Keep reusable logic in templates
If several workflows share container logic or a common execution unit, move that logic into `WorkflowTemplate` or `ClusterWorkflowTemplate` rather than duplicating the same YAML shape.

## Failure and control-flow notes

Model these behaviors deliberately instead of relying on defaults:
- retries
- timeouts
- exit handlers
- suspend steps for approval gates
- branching conditions

Important DAG note from the docs: Argo DAGs are fail-fast by default. Once a task fails, no new tasks are scheduled unless the workflow is modeled to handle that case.

## Review checklist

- Is this a `Workflow` or should it be a `CronWorkflow`?
- Would `steps` express intent more clearly than `dag`?
- Are parameters being misused to carry files?
- Should common logic move into a reusable template?
- Have retry, timeout, and cleanup behaviors been made explicit?
