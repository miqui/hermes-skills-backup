# Parallel PR fan-out on one repo (scaffold -> parallel halves -> review -> fix -> integrate)

Use when a greenfield project splits into independent modules that each ship as their own PR.

## Sequence
1. **Scaffold first, alone**: repo, CI (job names fixed up front), branch protection requiring those exact job names. Parallel work starts only after main exists and CI is green.
2. **Fan out one worker per module**, each in its own git worktree off fast-forwarded origin/main and its own branch. Give each worker exclusive ownership of one directory and forbid edits to shared entrypoints (e.g. `src/index.ts`) -- wiring is a later integration task.
3. **Pin the cross-module contract in the task text**: exact exported function names, signatures and shared types. Make the consumer take its dependency by injection (e.g. `verify` function passed in) and test against a local stub, so neither worker imports the other's code. Have the producer accept an injected shared instance (e.g. key store) so the integrator can wire one instance into both.
4. **Review before the human merge gate**: a read-only reviewer per PR set, against the relevant RFC/spec checklist. Reviewer output can be thin or self-contradictory (few API calls, hedged items) -- never apply it blindly.
5. **Fix pass**: the fix worker must verify each finding against the code first and report verified-real vs already-correct. Extra negative tests written in this pass tend to surface real bugs (e.g. a missing claim causing a 500 instead of 403) -- require them.
6. **Integration task** (wiring, e2e, docs with really-executed output) is dispatched only after the human merges the PRs.

## git-workflow.sh pitfalls in worktrees
- Do not pre-create the feature branch in the worktree: `change` creates the branch itself and fails if it exists. Use a detached HEAD, or delete the empty local branch, then run `change`.
- Use `update` (not `change`) to push follow-up commits to a branch that is already pushed with an open PR.
- Symlinking `node_modules` from the main checkout into a worktree is fine; keep it out of commits via `.git/info/exclude`.
- CodeRabbit may report "pass" while rate-limited -- it is not a review; do not count it.
