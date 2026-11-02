# Read-only Terraform policy scan (Checkov)

Use this as the baseline shape for a Terraform repository that needs a blocking
Checkov check on pull requests and the default branch. Resolve each action's
release tag to a full immutable SHA before committing; do not copy placeholder
SHAs unchanged.

```yaml
name: Checkov (Terraform IaC scan)

"on":
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  checkov:
    name: Checkov Terraform scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@<full-commit-sha> # vX.Y.Z
        with:
          persist-credentials: false

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@<full-commit-sha> # vX.Y.Z
        with:
          directory: terraform
          framework: terraform
          quiet: true
```

## Design choices

- `pull_request` safely covers fork PRs without base-repository write authority.
- `contents: read` is sufficient for source checkout and scanning.
- The action scans only the Terraform root. Do not recursively scan the entire
  repository unless that is intentional.
- Leave `soft_fail` unset/false so policy findings fail the check.
- Do not add SARIF uploads, PR comments, or provider credentials unless an
  explicit result-publication requirement justifies their additional scopes.

## Acceptance evidence

A parser can validate YAML but not the action runtime. Open a PR and verify the
completed GitHub Actions run shows successful checkout and Checkov steps. The
job should have pulled the pinned scanner image/action and exited with the
intended pass/fail conclusion.
