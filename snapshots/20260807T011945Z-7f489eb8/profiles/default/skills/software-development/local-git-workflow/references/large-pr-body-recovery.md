# Large PR Body Recovery

## Symptom

`git-workflow.sh change` can complete commit and push but fail while creating the PR:

```text
pull request create failed: GraphQL: Body is too long (maximum is 65536 characters) (createPullRequest)
```

This occurs when the generated `git diff --stat` is large, such as a full Hermes skill-corpus snapshot.

## Required Recovery

1. Treat the run as **partial success**: branch and commit may already exist on `origin`.
2. Inspect current branch, `HEAD`, and worktree. Do not create a second branch or use raw `gh pr create`.
3. Ensure the wrapper has the bounded PR-body generator and `pr` command.
4. Syntax-check wrapper before use:

   ```bash
   bash -n /Users/miqui/development/scripts/git-workflow.sh
   ```

5. Resume through the wrapper from the already-pushed feature branch:

   ```bash
   bash /Users/miqui/development/scripts/git-workflow.sh pr "<PR title>"
   ```

6. Independently verify the resulting PR URL, state, base, and head branch.

## Guardrails

- The wrapper limits its generated diff-stat section below GitHub's 65,536-character PR-body limit.
- Never bypass the wrapper with a direct `gh pr create` call.
- If `pr` fails, surface its exact output and ask the user how to proceed.
