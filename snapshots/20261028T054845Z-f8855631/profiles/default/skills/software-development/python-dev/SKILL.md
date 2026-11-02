---
name: python-dev
description: Use when building or modifying Python projects, services, Lambda handlers, or CLIs with Hermes-native repo inspection, uv-based workflows, typing, testing, and deployment hygiene.
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, fastapi, lambda, cli, uv, typing, testing, docker]
    related_skills: [test-driven-development, systematic-debugging, python-debugpy, requesting-code-review]
---

# Python Development

## Overview

Use this skill when Hermes is asked to inspect, build, modify, or standardize Python codebases. It is for implementation work: discover the actual project structure, identify the active toolchain, edit the right files, run the right checks, and leave the repo in a verifiable state.

The core stance is Hermes-native and repo-first: inspect before editing, prefer the repository's existing conventions when they are coherent, use Hermes file tools for code work, and verify before declaring success.

## When to Use

- Building or editing Python applications or libraries
- Adding or changing FastAPI endpoints
- Writing or fixing AWS Lambda handlers in Python
- Building CLI tools with typer, argparse, click, or rich
- Creating or cleaning up Python project structure
- Adding tests, typing, packaging, or Docker assets
- Modernizing older Python repos toward `pyproject.toml` + `uv`

Do not use this skill for:
- Pure planning with no implementation changes
- Non-Python projects
- Deep root-cause debugging when `systematic-debugging` should drive the task
- Strict test-first execution when `test-driven-development` should be primary

## Hermes Workflow

### 1. Inspect before editing

Do not assume layout, toolchain, or test commands. Inspect the repo first:

- find Python files and project manifests
- read `pyproject.toml`, `README.md`, and relevant config files
- identify framework and entrypoints from actual code
- reuse existing repo conventions when they are coherent

Typical discovery targets:

- `pyproject.toml`
- `uv.lock`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- `pytest.ini`
- `mypy.ini`
- `ruff.toml` or `.ruff.toml`
- `.env.example`
- `Dockerfile`
- `README.md`
- likely entrypoints such as `app/main.py`, `main.py`, `handler.py`, or `cli/main.py`

### 2. Prefer Hermes file tools for code work

Use:

- `search_files` to discover files and patterns
- `read_file` to inspect code and config
- `patch` for targeted edits
- `write_file` for full-file creation or rewrites
- `terminal` only for commands that must execute: tests, linters, package tools, git status, Docker builds

### 3. Match the repo before imposing a template

If the repo already uses a coherent stack, extend it instead of forcing a different one.

Examples:
- keep `pytest` if the repo uses `pytest`
- keep `ruff` if the repo uses `ruff`
- keep the current package layout if imports and tooling depend on it
- only introduce `uv` or `pyproject.toml` migration when the task asks for it or the repo is clearly under-structured

### 4. Verify with the real project commands

Before finishing, run the smallest meaningful verification available:

- targeted test for changed behavior
- broader test or suite when feasible
- lint or type checks if configured
- import or startup smoke test if no formal tests exist

Report what ran and what remains unverified.

## Opinionated Defaults for New Projects

When creating a new Python project from scratch and the user has not specified a different stack, prefer:

- Python 3.11+
- `uv` for dependency management and execution
- `pyproject.toml` as the source of truth
- `pytest` for tests
- `ruff` for linting and formatting
- `mypy` when the codebase benefits from static typing checks
- FastAPI for HTTP APIs
- Pydantic v2 for schema validation
- typer for CLIs
- rich for CLI output
- `.env.example` for local environment documentation

These are greenfield defaults, not a reason to rewrite an established repo that already has coherent conventions.

## Python Decision Rules

### Dependency management

Prefer `uv` for new or modernized Python projects.

Guidance:
- keep `pyproject.toml` as the source of truth
- avoid ad hoc `pip install` flows for project dependencies
- only generate `requirements.txt` when an external deploy target truly requires it
- if the repo uses a `src/` layout, include a `[build-system]` table in `pyproject.toml`; otherwise `uv sync` can install dependencies without installing the project itself, leaving the application package off import resolution
- when creating a local `.venv`, prefer targeting that interpreter explicitly for installs if there is any ambiguity about the active environment

Example:

```bash
uv venv
uv pip install --python .venv/bin/python -e .[dev]
```

This is safer than assuming `uv pip install -e .[dev]` will always target the intended project venv, especially on hosts that may already have another active Python environment.

For starter structure and settings, use `references/pyproject-template.md`.

### Framework detection

Infer the project type from the repo before editing:

- FastAPI: look for `FastAPI`, `APIRouter`, `uvicorn`
- Lambda: look for `handler(event, context)`, `template.yaml`, SAM/CDK/serverless files
- CLI: look for `typer`, `click`, `argparse`, or `__main__` entrypoints

For opinionated greenfield layouts, use:
- `references/fastapi-layout.md`
- `references/fastapi-production-patterns.md` when a FastAPI service needs deeper production wiring guidance
- `references/fastapi-cloudrun-firestore.md` when the service is a small GCP/Cloud Run/Firestore showcase and should document env-driven deploy inputs plus credential handling clearly
- `references/lambda-layout.md`
- `references/cli-layout.md`

### Typing and structure

- add parameter and return annotations to new or edited functions
- prefer concrete types over `Any`
- keep modules focused
- separate interface code from business logic when the codebase size justifies it
- avoid turning `utils.py` into a catch-all module

### Configuration and secrets

- read secrets and environment-specific config from environment variables
- provide `.env.example` when local setup needs configuration
- do not hardcode tokens, passwords, or deployment-specific values

### Logging

- follow existing logging conventions in the repo
- if no convention exists, prefer centralized or structured logging over scattered prints
- remove temporary debug prints before finishing

## Verification and Packaging

Prefer the repo's existing test entrypoint. If none is documented, infer it from the manifest and filesystem.

Verification order:
1. run focused checks for the changed area
2. run broader checks if they are fast and available
3. if no test suite exists, run the lightest useful smoke test
4. report what was run, what passed, and any remaining gaps

For reusable verification guidance, use `references/verification-playbook.md`.

If the user explicitly wants TDD, load and follow `test-driven-development` as the primary execution model.

Add Docker assets when the project is deployable as a service or the task asks for containerization.

General guidance:
- prefer multi-stage builds
- use slim base images
- run as non-root when practical
- copy only what the runtime needs
- include `.dockerignore`
- lint Dockerfiles when `hadolint` is available

For starter Dockerfile guidance, use `references/dockerfile-template.md`.

## README Expectations

When creating or substantially changing a Python project, ensure `README.md` covers the actual workflow used by the repo:

- project purpose
- prerequisites
- install/setup commands
- local run commands
- environment variables
- test commands
- deployment notes when relevant

Do not paste generic instructions that do not match the repository.

## Included References

This skill ships with linked references for reusable detail:

- `references/greenfield-project-checklist.md` — greenfield Python project checklist
- `references/pyproject-template.md` — starter `pyproject.toml` structure for uv/pytest/ruff/mypy
- `references/fastapi-layout.md` — opinionated FastAPI file/layout guidance
- `references/fastapi-production-patterns.md` — deeper FastAPI production patterns for settings, async SQLAlchemy, DI boundaries, auth, error handling, and tests
- `references/fastapi-cloudrun-firestore.md` — greenfield pattern for small FastAPI services deployed to Cloud Run with Firestore, env-driven Terraform inputs, repository mocking for tests, and a moderate-concurrency baseline
- `references/lambda-layout.md` — opinionated AWS Lambda file/layout guidance
- `references/cli-layout.md` — opinionated Python CLI file/layout guidance
- `references/dockerfile-template.md` — Python container/Dockerfile starter guidance
- `references/verification-playbook.md` — lightweight verification flow for Python changes
- `references/bypass-construction-and-atomic-failure-tests.md` — worked example: bypass-constructing a frozen dataclass to test defense-in-depth validators, plus atomic-write (`os.replace`) failure-path test patterns

## Host-Specific Rules

### New project location

When creating a new project on this host, place it under:

```bash
/Users/miqui/development
```

### Git workflow on hosts with a required wrapper

If repository creation, push, or PR actions in the active environment must go through a local wrapper, load and follow `local-git-workflow` instead of embedding the host-specific policy here.

## Suggested External References

Use or cite these when deeper framework- or tooling-specific guidance is needed:

- Python packaging and `pyproject.toml`: https://packaging.python.org/
- Astral `uv` docs: https://docs.astral.sh/uv/
- Pytest docs: https://docs.pytest.org/
- Ruff docs: https://docs.astral.sh/ruff/
- FastAPI docs: https://fastapi.tiangolo.com/
- Pydantic docs: https://docs.pydantic.dev/
- Typer docs: https://typer.tiangolo.com/
- Python Morsels articles: https://www.pythonmorsels.com/articles/browse/ — practical advice on idiomatic Python, iteration, refactoring, and readable function design
- AWS Lambda Python docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html

## Common Pitfalls

1. Editing before inspecting the repo's actual layout and tooling
2. Forcing a new stack onto a repo that already has coherent conventions
3. Using shell text-processing instead of Hermes file tools for code inspection and edits
4. Adding dependencies without updating the project manifest
5. Leaving functions untyped in otherwise typed code
6. Hardcoding secrets or environment-specific configuration
7. Declaring success without running meaningful verification
8. Writing generic README or Docker instructions that do not match the repo
9. Using raw git or PR commands when the host requires a dedicated local wrapper skill such as `local-git-workflow`
10. Assuming `uv pip install` will target the project `.venv` without verification
11. Documenting `uv` commands that differ from the interpreter path actually used during verification
12. Planning modules under a `code/` source directory without first probing imports. Top-level `code` collides with Python's standard-library `code` module, so do a no-write import-path preflight before locking task paths. For a script invoked as `python code/main.py`, treat `code/` as the source root and configure pytest with `pythonpath = ["code"]` so tests import `router...`; do not assume `code.router...` is importable unless the project deliberately creates that package boundary.

## Closing Validation Bypasses (Defense in Depth)

When the task is specifically "close a bypass" in validation/security-check code (e.g. a blank/null field, a path-traversal edge case, an unresolved reference that silently passes instead of failing), pair `test-driven-development` with this stricter sequence:

1. **Write the RED test against the *current*, unpatched code and run it before touching implementation.** The failure must reproduce the exact defect (e.g. `report.is_fatal is False` where it should be `True`), not a generic "feature missing" error. This is the evidence the bypass is real.
2. **Check every layer that can independently reach the bad state, not just the first one you found.** A single malformed value often has more than one path to it — e.g. a catalog row that is directly malformed AND a downstream record that merely references that row. Add a RED test (and a fix) for each path before declaring the bypass closed; fixing only the first path you noticed leaves the second one open.
3. **Hunt for "last-row-wins" bugs in any `{key: row for row in rows}`-style dict comprehension used to build an id lookup.** This is the single most common way an ambiguity check gets silently defeated: a blank or duplicate id doesn't raise, it just gets overwritten by whichever row is read last. Write a RED test where the *first* row for a duplicated id is broken (missing file, None field) and the *second* is valid — the fix must still report the duplicate as fatal, not let the downstream reference "resolve cleanly" because the last row happened to be good. Fix by rejecting/excluding ambiguous ids from the lookup (or building it with an explicit `seen` set row-by-row) rather than trusting a naive comprehension.
4. **If the fix renames or splits an existing check/finding name for clarity** (e.g. one generic `x_file_path_missing` becoming three distinct `x_path_blank` / `x_path_escapes_root` / `x_file_missing` checks so the diagnostic tells you exactly what's wrong), update the *existing* test(s) asserting the old name as part of the RED step — don't treat that as a separate afterthought. Expect that old-name assertion to go RED alongside your new tests; that's the correct signal, not a regression.
5. **Verify GREEN at three levels:** the new targeted test(s), the full existing test suite (regression check — some other test may already exercise the same code you touched), and, if real/sample project data is available, a smoke run of the fixed validation against that real data to confirm no false positives were introduced on legitimate input.
6. **Confirm repo hygiene before calling it done:** `git status --short` / `git diff --check` to ensure only intended files changed, plus lockfile consistency (`uv lock --check`, etc.) if the project has one.
7. When a `terminal` command needs interactive approval (e.g. `python -c "..."` one-liners, or `rm`), write the script to a scratch file with `write_file` and run `python /path/to/script.py` instead of fighting the approval prompt — this is faster than re-arguing with the sandbox and keeps the smoke-check reproducible.

## Defense-in-Depth Validation and Atomic-Write Failure-Path Testing

When the bypass being closed is specifically "an outer validator trusts an
inner one instead of independently re-checking" (e.g. a CSV/JSON writer
that only checks `isinstance(record, SomeFrozenDataclass)` and relies on
that dataclass's own `__post_init__` for field-level correctness), or the
task is "prove an atomic-write claim, don't just assert it":

1. **Bypass-construct the frozen dataclass to defeat its own
   `__post_init__`.** Building a normal instance can never carry invalid
   field values if the dataclass validates itself at construction time —
   you need an instance that skips that validation entirely:
   ```python
   def _bypass_construct(cls, **kwargs):
       obj = object.__new__(cls)
       for f in fields(cls):
           object.__setattr__(obj, f.name, kwargs[f.name])
       return obj
   ```
   Feed it invalid values (invalid enum, out-of-range/non-finite/bool
   confidence, wrong type) and assert the *outer* validator still raises
   its own public error type. If the outer layer only trusted
   `isinstance` + the inner `__post_init__`, this test goes RED first —
   that's the proof the defense-in-depth is missing, not a test bug.
2. **Cover the full numeric edge set for any confidence/score-style
   field**, not just "out of [0,1] range": non-numeric (e.g. a string),
   `bool` (subclass of `int` in Python — `isinstance(x, int)` alone will
   wrongly accept `True`/`False`), `math.nan`, and `math.inf`/`-math.inf`.
   Use `math.isfinite(x)` in the fix, not a bare range check, since NaN
   passes `0 <= nan <= 1` as `False` correctly but `-inf`/`inf` do not
   reliably fail a naive comparison across all callers.
3. **Add a "wrong type in the iterable" test for every public write
   function**, not just the validator: pass a plain object (not the
   expected dataclass) into the writer and assert it raises the writer's
   own public error *and* produces zero write artifacts (no output file,
   no partial file) — this is different from, and in addition to, testing
   the validator function alone.
4. **Prove atomic-write failure cleanup by monkeypatching the swap
   primitive itself** (`os.replace`), not the write step:
   ```python
   def _boom(src, dst):
       raise OSError("simulated os.replace failure")
   monkeypatch.setattr(os, "replace", _boom)
   with pytest.raises(OSError):
       write_fn(...)
   assert target_path.read_text() == original_content  # untouched
   assert [p.name for p in tmp_path.iterdir()] == [target_path.name]  # no temp leftovers
   ```
   This is the only way to verify the documented "temp file + fsync +
   os.replace, existing target left byte-for-byte unchanged on failure"
   contract; asserting it only in a docstring is not verification.
5. Full worked example (module structure, all RED failures observed, the
   three validator functions added, and the final GREEN/full-suite/
   real-dataset-scale verification) is in
   `references/bypass-construction-and-atomic-failure-tests.md`.

## Repairing Conflated Deterministic Signals

When the task is "field X is supposed to be independent of field Y but the
implementation accidentally derived X from Y" (e.g. a "recency" flag that
was really just checking "no opt-out present", a "verified" flag that was
really just checking "not blank"), treat it as a bypass-closing task and
pair `test-driven-development` with this sequence:

1. **Confirm the anchor.** If the correct signal is time-based ("recent
   relative to what?"), find or introduce an explicit anchor value from the
   domain data (e.g. the incoming record's own timestamp) — never real
   wall-clock time (`datetime.now()`/`time.time()`). Wall-clock anchors make
   the system's output depend on when it happens to run, which breaks the
   "deterministic given the same input" requirement almost every dataset
   task in this class implicitly needs.
2. **Write RED fixtures that vary one dimension at a time**, holding the
   other constant in both directions:
   - true-condition-1 with false-condition-2 (proves condition-1 isn't a
     proxy for condition-2's absence)
   - false-condition-1 with true-condition-2 (proves the reverse)
   - a boundary/edge case on the newly-introduced comparison itself: value
     *after* the anchor (future relative to anchor), and a malformed/
     unparseable value for either side. These are exactly what a naive fix
     (bare `strptime` without error handling, wrong anchor direction) gets
     wrong silently.
   - when the threshold is day-granular (e.g. "within N days"), add a pair
     of fixtures that isolate whole-day truncation specifically: one
     exactly N days 0 hours before the anchor (must be inside the window),
     and one N days plus a nonzero fractional remainder before the anchor,
     e.g. N days 23 hours (must be outside the window). A comparison that
     truncates the elapsed duration to whole days first — `(anchor -
     value).days <= N` — silently treats both as "exactly N days" and
     wrongly includes the second one. Only comparing the full `timedelta`
     object against `timedelta(days=N)` (never `.days`) gets the boundary
     right. Confirm the truncating form actually produces the wrong
     RED/GREEN result on these two fixtures before trusting any fix that
     touches a day-based recency/expiry/staleness threshold.
   Run the full set against the *unfixed* code and confirm every one of
   them fails for the conflation reason, not just the obvious case — that's
   what proves you found the actual coupling, not one symptom of it.
3. **Implement the fix as an explicit, named, documented threshold/anchor**
   (e.g. a module-level `_RECENCY_THRESHOLD_DAYS` constant with a comment
   justifying the value, and a small `_parse_timestamp`/`_is_recent_x`
   helper that fails safe — returns the conservative/false value — on
   missing or unparseable input rather than raising). Never let a malformed
   timestamp propagate as an exception into the caller. For day-based
   thresholds, compare the full elapsed `timedelta` against
   `timedelta(days=N)` directly (`elapsed <= timedelta(days=N)`), not
   `elapsed.days <= N` — the latter always rounds toward "more recent than
   it really is" and silently breaks exact-boundary precision.
4. Verify GREEN at the same three levels as bypass-closing work: targeted
   tests, full suite, and — when real dataset/project data is available —
   a smoke run over every real row confirming zero exceptions and a
   plausible distribution of the now-decoupled signal (e.g. count how many
   real records are "recent-but-opted-out" to confirm the decoupling
   actually changes real output, not just fixture output).

## Verification Checklist

- [ ] Repo structure and tooling were inspected before edits
- [ ] Changes match the repo's existing conventions or intentionally improve them
- [ ] Dependencies and config were updated in the right files
- [ ] New or changed Python code includes appropriate typing
- [ ] The changed behavior was verified with tests, linting, or smoke checks
- [ ] Any README or Docker updates match the actual project workflow
- [ ] Any required repo creation, push, or PR action uses `local-git-workflow` when the active host mandates a wrapper-based workflow
