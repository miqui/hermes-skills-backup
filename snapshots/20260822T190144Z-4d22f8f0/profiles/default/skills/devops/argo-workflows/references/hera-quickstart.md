# Hera Quick Start for Argo Workflows

Hera is the Python SDK for Argo Workflows. In this taxonomy it belongs inside `devops/argo-workflows`, not as a separate top-level skill, because it is a Python authoring surface for Kubernetes workflow execution.

## Source Basis

Derived from:
- Hera quick start: `https://hera.readthedocs.io/en/stable/walk-through/quick-start/`
- Argo Workflows walkthrough patterns used by Hera-generated workflows

## When to use Hera

Use Hera when:
- workflow specs benefit from Python composition
- you want reusable Python abstractions around repeated workflow patterns
- a team already maintains Python tooling around the workflow lifecycle

Prefer plain YAML when:
- the workflow should stay maximally transparent to platform operators
- code abstraction adds little value
- Git review readability is more important than Python composition

## Minimal local setup pattern

The quick start uses this flow:

```bash
pip install hera
kubectl -n argo port-forward service/argo-server 2746:2746
```

Then author a workflow in Python and submit it via `w.create()`.

## Minimal example

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

## Working style guidance

### Good fits for Hera
- generating families of similar workflows
- wrapping common task patterns in Python helpers
- integrating workflow authoring into an existing Python codebase

### Cases where YAML is still better
- small static workflows
- troubleshooting where rendered manifest clarity matters most
- handoff to teams that expect raw Kubernetes objects in review

## Troubleshooting Hera-specific issues

Check these first:
- local port-forward still active
- host and auth/token configuration are correct
- the generated workflow matches the intended YAML semantics
- container images referenced by Hera-generated templates exist and are pullable

## Practical advice

1. Keep the YAML mental model even when writing Python.
2. Debug the rendered workflow shape when behavior is surprising.
3. Do not let Python abstractions obscure namespace, template, or dependency errors.
4. Pair with `python-dev` only when the problem extends beyond workflow authoring itself.
