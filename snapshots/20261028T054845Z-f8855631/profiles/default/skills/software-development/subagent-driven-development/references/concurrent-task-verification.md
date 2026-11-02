# Concurrent Task Verification

Use this reference when implementation, repair, and review agents overlap in time.

## Establish ownership before overlapping work

1. State the exact files each active worker may modify.
2. Run concurrent work only when file ownership is disjoint, or when one task is strictly read-only.
3. If a delayed review finds a mandatory defect, repair it even if the user bypassed its original gate. It may run in parallel with a later task only if the repair’s files and valid-input public behavior remain isolated from the later task.
4. Tell reviewers to exclude active work-in-progress paths from their conclusion.

## Interpret suite failures correctly

A full suite can fail legitimately while a test-first worker has created new tests before its implementation exists. Do not call this a regression without attribution.

1. Inspect the failure set and identify the owning active task.
2. Run the repaired task’s focused suite plus a combined suite that excludes only the explicitly identified WIP tests.
3. Record the exclusion and reason, e.g. `198 passed, 21 Task-7 CLI tests excluded while main.py implementation is active`.
4. Do not accept the overall integration until every active writer has completed and the unrestricted full suite passes.

## Review sequencing under concurrency

- A task’s strict/quality reviewer receives the task’s original contract, exact owned files, and an explicit instruction not to assess unrelated WIP paths.
- When a review is delayed, distinguish the task’s historical acceptance state from its current repair state. A clear user direction to proceed makes a review non-blocking; it does not waive a defect found later.
- After a repair, require focused RED/GREEN evidence, independent rerun, strict re-review, then quality review.

## Evidence to preserve

For each isolated repair or task:

- before/after test counts and commands;
- any intentionally excluded WIP tests and their owner;
- direct smoke result that does not create prohibited artifacts;
- final full-suite result after all concurrent writers settle.
