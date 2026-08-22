# Coding Agent Architecture Reference

## Overview

This reference captures reusable architecture patterns for coding agents that work inside real repositories.

Use it when you need to design or review:
- a repo-aware bug fixer
- a test repair agent
- a refactoring agent
- a PR review agent
- a CI failure investigator
- a codebase exploration agent

The goal is to keep the coding loop **small, inspectable, and verifiable**.

## The Core Loop

A reliable coding agent usually follows this sequence:

1. **Scope the task**
   - identify the bug, feature, or review target
   - bound the expected files and commands

2. **Inspect the repo**
   - search code
   - read relevant files
   - inspect failing tests or logs
   - inspect git diff/status if relevant

3. **Form a hypothesis**
   - what is broken?
   - what is the smallest plausible fix?

4. **Make a narrow change**
   - patch one file or a tightly coupled set of files
   - avoid broad edits before evidence exists

5. **Run targeted verification**
   - run the smallest test/lint/build command that proves or falsifies the hypothesis

6. **Interpret the result**
   - success → summarize and check for unintended regressions
   - failure → revise the hypothesis and try again

7. **Finalize carefully**
   - inspect diff
   - note remaining risks
   - report exactly what changed and how it was verified

## Recommended Layers

### 1. Planner / task interpreter
Responsibilities:
- classify the job (bug fix, refactor, review, etc.)
- choose whether to inspect, edit, or verify next
- keep the task bounded

### 2. Repo inspection layer
Common tools:
- `search_code(query, glob?, limit?)`
- `read_file(path)`
- `git_status()`
- `git_diff(base?)`
- `read_test_output(path)`

Design guidance:
- prefer narrow reads over dumping whole repos
- preserve path context in outputs

### 3. Edit layer
Common tools:
- `patch_file(path, patch)`
- `write_file(path, content)`
- `create_file(path, content)`

Design guidance:
- prefer minimal diffs
- preserve formatting and style
- avoid giant generated rewrites unless the task explicitly needs them

### 4. Execution / verification layer
Common tools:
- `run_tests(scope)`
- `run_lint(scope)`
- `run_build(scope)`
- `run_command(command, allowlist_tag)`

Design guidance:
- start with narrow, allowlisted commands
- return exit code, stdout, stderr, and timing if possible
- make failures explicit and structured

### 5. Policy / safety layer
Responsibilities:
- restrict dangerous shell commands
- gate network access
- require approval for destructive actions
- block unrelated repo mutations

### 6. State / memory layer
Keep these separate:
- task state
- working memory / hypotheses
- durable repo conventions
- external context like issues or CI logs

### 7. Observability layer
Record:
- prompts and high-level decisions
- tools called
- files touched
- commands executed
- retries and failures
- final verification evidence

## Minimum Viable Coding Agent

A good starter coding agent only needs:
- repo search
- file read
- patch/write
- run tests
- inspect diff

That is enough for many bug-fix and test-repair tasks.

## Suggested Tool Contracts

### Good
- `search_code(query, glob, limit)`
- `read_file(path)`
- `patch_file(path, patch)`
- `run_tests(scope)`
- `get_git_diff(base_ref)`

### Bad
- `fix_repo(prompt)`
- `use_terminal_for_anything(goal)`
- `solve_bug(task_blob)`

Good coding-agent systems expose **small engineering primitives**, not disguised prompts.

## Suggested Output Shape for Tool Calls

Where possible, return structured data like:

```json
{
  "ok": true,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "files_changed": ["src/auth.py"],
  "summary": "pytest auth tests passed"
}
```

This makes the next reasoning step more stable than dumping raw text alone.

## Verification Patterns

### Bug-fix pattern
1. reproduce failure
2. inspect relevant code
3. patch minimally
4. run targeted tests
5. inspect diff
6. optionally run broader checks

### Refactor pattern
1. inspect current behavior
2. identify invariants
3. refactor one slice at a time
4. run tests after each slice
5. inspect diff for unintended spread

### PR review pattern
1. inspect diff first
2. read changed files only as needed
3. classify findings by severity
4. verify suspicious behavior with code or tests when possible

### CI-failure pattern
1. read failing log
2. isolate failing command/test
3. inspect affected files
4. patch minimally
5. rerun the narrow failing step first

## Architecture Decisions by Maturity

### Early prototype
- one agent
- 4-8 tools
- no long-term memory
- narrow test command
- local logs only

### Internal tool
- one or two agent roles
- stronger verification
- policy boundaries
- persistent task state
- artifact logging

### Production coding-agent product
- role separation if needed
- strong tracing
- approval policy
- sandboxing
- retry budgets
- evaluation harness
- regression checks

## Common Pitfalls

1. **Starting with too many tools**
   The model gets confused and tool choice quality drops.

2. **No explicit diff inspection**
   Big unintended edits slip through.

3. **Treating test output as unstructured noise**
   Parse and summarize it enough to support the next step.

4. **Skipping targeted reruns**
   Whole-suite runs are expensive and slow down iteration.

5. **Allowing arbitrary shell too early**
   Expand permissions only after the basic loop is reliable.

6. **Building multi-agent systems before one loop works**
   Reliability must come before orchestration complexity.

## Verification Checklist

- [ ] The task class is explicit.
- [ ] Repo inspection tools are narrow and sufficient.
- [ ] Edit tools are narrow and reviewable.
- [ ] Verification commands are targeted.
- [ ] Tool outputs are structured enough for reuse.
- [ ] Diff inspection is part of the loop.
- [ ] Safety boundaries are explicit.
- [ ] Logs capture decisions, tool calls, and evidence.
