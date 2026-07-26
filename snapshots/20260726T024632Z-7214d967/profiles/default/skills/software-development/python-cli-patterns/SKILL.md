---
name: python-cli-patterns
description: Use when designing, building, refactoring, or reviewing Python command-line tools so they are ergonomic, composable, testable, and production-friendly.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, cli, typer, argparse, click, uv, pyproject, rich, testing, packaging]
    related_skills: [python-dev, test-driven-development, requesting-code-review, secure-agent-skills]
---

# Python CLI Patterns

## Overview

Use this skill when creating or improving Python command-line tools that people will run directly from a shell, CI job, cron task, or automation pipeline. The goal is not merely to make a command “work,” but to make it predictable, discoverable, scriptable, and easy to maintain.

A strong Python CLI has a thin command layer, typed core logic, stable output modes, clear help text, sensible exit behavior, and tests that cover both happy paths and operational failures. This skill is intentionally opinionated for greenfield work while still respecting coherent conventions in an existing repository.

The stance here matches the local Python catalog direction: prefer **modern Python**, **`uv`**, **`pyproject.toml`**, **pytest**, **ruff**, and a **Typer-first** CLI approach unless the repo or deployment constraints clearly justify something lighter or older.

## When to Use

- Building a new Python CLI from scratch
- Refactoring a script into a reusable command-line tool
- Designing subcommands, flags, and argument conventions
- Adding machine-readable output to an existing CLI
- Improving help text, exit codes, logging, or error behavior
- Preparing a CLI for packaging, CI, cron, or team use
- Reviewing a Python CLI for maintainability and UX quality

Do not use this skill for:

- General Python service or library work with no CLI surface
- One-off throwaway scripts that will never be reused
- Pure planning with no implementation path
- Deep root-cause debugging where `systematic-debugging` should lead
- Broad Python repo work where `python-dev` should be the primary skill

## Greenfield Defaults

When building a new CLI and the user has not asked for a different stack, prefer:

- Python **3.11+**
- `uv` for dependency management and execution
- `pyproject.toml` as the source of truth
- `typer` for the CLI framework
- `rich` for human-friendly terminal output when helpful
- `pytest` for tests
- `ruff` for linting and formatting
- `mypy` when the codebase is more than trivial or benefits from stronger interfaces
- `src/` layout for reusable/distributable tools
- console script entry points in `pyproject.toml`

These are greenfield defaults, not a reason to rewrite a coherent repo that already uses Click, argparse, hatchling, Poetry, or another established stack.

## Decision Rules

### Framework choice

Use the lightest framework that fits the problem.

| Situation | Preferred choice | Why |
| --- | --- | --- |
| Greenfield team-facing CLI with subcommands/options and good UX needs | `typer` | Excellent ergonomics, type hints, help generation |
| Mature existing project already using Click | `click` | Match the repo instead of forcing migration |
| Standard-library-only requirement or minimal dependency footprint | `argparse` | No extra dependency, portable, stable |
| Very small single-purpose utility | `argparse` or `typer` | Keep it simple |

Default recommendation for new shared tools: **Typer + Rich + pytest + uv**.

### Dependency management

Prefer `uv` for new CLIs.

Good patterns:
- keep `pyproject.toml` as the source of truth
- use `uv sync` to realize the environment
- use `uv run ...` for commands
- use explicit interpreter targeting when a local `.venv` selection is ambiguous

Example:

```bash
uv sync --dev
uv run pytest
uvx ruff check .
uv run mypy .
```

If the active host environment conflicts with the project venv, verify which interpreter `uv` is using before assuming installs landed where you expect.

### Packaging

For reusable tools, expose a console script entry point instead of requiring `python path/to/script.py`.

Prefer:
- package import path under `src/`
- a short public command name
- one documented installation and execution path

## Hermes Workflow

### 1) Inspect before editing

Do not assume the project layout or CLI framework. Inspect the repo first.

Discovery targets:
- `pyproject.toml`
- `uv.lock`
- `requirements.txt`
- `setup.py` / `setup.cfg`
- `README.md`
- `tests/`
- CLI entrypoints such as `main.py`, `cli.py`, `__main__.py`
- parser/framework markers like `Typer()`, `click.command`, `ArgumentParser`

### 2) Keep the CLI boundary thin

The command layer should parse input, call business logic, and format output. It should not contain the entire program.

Good separation:
- `cli.py` or `main.py`: command definitions and top-level exception mapping
- `core/`, `services/`, or equivalent: actual work
- typed data models if the domain is non-trivial

Avoid stuffing file I/O, HTTP calls, parsing, formatting, and business rules all into a single command callback.

### 3) Design for both humans and automation

Every non-trivial CLI should answer yes to these:
- can a human discover it from `--help`?
- can a script call it reliably?
- is stdout stable enough for piping?
- are failures non-zero and understandable?

### 4) Verify before declaring success

Run the lightest meaningful verification:
- focused CLI test
- broader test file/package
- lint and type checks when configured
- smoke test if no formal tests exist

Report what ran and what remains unverified.

## Project Shape

For reusable CLIs, prefer a structure close to:

```text
project/
  pyproject.toml
  README.md
  src/mytool/
    __init__.py
    cli.py
    main.py
    core/
    services/
  tests/
    test_cli.py
    test_core.py
```

Guidance:
- `cli.py` defines commands and top-level presentation
- `main.py` provides a minimal executable entrypoint if needed
- `core/` or `services/` contains reusable logic
- tests should cover both command behavior and non-CLI logic

## Command Design Patterns

### Single-purpose command

Use when the tool does one thing well.

Examples:
- `slugify`
- `validate-config`
- `render-report`

Pattern:

```text
tool [OPTIONS] INPUT
```

### Resource + verb subcommands

Use for broader tools with multiple entities.

Examples:

```text
tool user create ...
tool user list ...
tool config validate ...
tool project init ...
```

Keep naming consistent across resources.

### Action-oriented subcommands

Use when actions matter more than resource modeling.

Examples:

```text
tool sync
tool doctor
tool export
tool migrate
```

### Output-mode flags

If a command serves both humans and automation, make the mode explicit.

Typical patterns:

```text
--json
--format json|yaml|table
--quiet
--verbose
```

Do not mix decorative human text into output intended for programmatic consumption.

## Output, Errors, and Exit Codes

### stdout vs stderr

- write result data to **stdout**
- write warnings, progress, and errors to **stderr**
- keep stdout stable enough for pipes and scripts
- ensure JSON mode writes only JSON to stdout

### Wrapping pager-oriented or terminal-formatted commands

When your CLI is a thin wrapper around an external Unix command, verify the real output shape in non-interactive mode instead of assuming environment variables are sufficient.

Example class:
- `man`
- commands that detect TTY vs pipe behavior
- tools that emit backspace overstrike or other terminal-era formatting when not using their usual pager

A durable pattern:
1. force non-interactive behavior explicitly with env vars such as `PAGER=cat` or `MANPAGER=cat` when appropriate
2. capture stdout/stderr so your CLI, not the child process, owns final presentation
3. verify the raw output in a real smoke test
4. if the command still emits formatting artifacts, normalize before writing to stdout

Important macOS-specific example:
- `man` with pager disabled can still emit overstrike text like `N\bNA\bAM\bME\bE`
- for a plain-text wrapper, post-process through `col -bx` when available before writing to stdout
- if the normalizer is unavailable or fails, fall back to the original output rather than crashing
- after normalization, if the wrapper is intended for LLM or automation consumption, consider targeted section filtering rather than raw pass-through. For `man`, a useful default is to drop trailing metadata sections like `AUTHOR`, `REPORTING BUGS`, and `COPYRIGHT`, while keeping only the `SEE ALSO` line that begins with `Full documentation`.

This pattern matters for CLIs intended for piping, automation, LLM consumption, or log capture.

### Human-readable output

Use concise, scan-friendly text. Tables and Rich formatting are good for interactive terminals when they do not interfere with automation.

### Machine-readable output

Prefer JSON for automation.

Rules:
- emit only JSON in JSON mode
- avoid trailing commentary
- keep field names stable
- do not let progress bars or banners pollute stdout

### Exit behavior

At minimum:
- `0` = success
- non-zero = failure

Recommended baseline distinctions for non-trivial tools:
- `1` = general/runtime failure
- `2` = invalid usage or argument validation failure
- `3` = dependency/network/backend failure
- `4` = requested resource/state not found

Do not invent a large exit-code taxonomy unless users truly need it.

### Error handling

- validate user input early
- catch expected operational failures near the boundary
- print short, actionable error messages to stderr
- reserve tracebacks for debug mode or unexpected faults

Good:

```text
Error: config file not found: /path/to/config.yaml
Hint: pass --config-path or run `tool init` first.
```

## Naming and Option Conventions

### Commands

- prefer short, recognizable verbs: `list`, `get`, `create`, `delete`, `validate`, `export`
- avoid synonyms unless they add real value
- keep nesting shallow unless the domain clearly needs more structure

### Options

- prefer descriptive long names: `--config-path`, `--output-dir`
- add short flags only for common/high-frequency cases: `-h`, `-v`, `-q`, `-o`
- prefer kebab-case in the CLI surface
- avoid cryptic one-letter flags

### Boolean flags

Prefer explicit behavior flags.

Good:
- `--dry-run`
- `--force`
- `--yes`
- `--no-color`

### Positional arguments

Use positionals for required, obvious inputs. Use named flags for everything that benefits from clarity.

Good:

```text
mytool render template.md --output out.html
```

Avoid dense positional bundles that make call sites hard to remember or read.

## Help Text and Discoverability

Help text should be useful without source inspection.

For each command include:
- one concise purpose line
- meaningful option descriptions
- examples for non-obvious usage
- defaults when they materially affect behavior

Good help line:
- `Validate a project configuration file and report schema errors.`

Weak help line:
- `Run the command.`

## Logging and Verbosity

Distinguish command results from diagnostics.

Recommended pattern:
- default: concise output
- `--verbose`: more operational detail
- `--quiet`: suppress non-essential text
- `--debug`: enable tracebacks or deeper diagnostics

Avoid scattering raw `print()` statements throughout the code. Prefer centralized output or logging helpers so stdout/stderr discipline remains consistent.

## Configuration and Environment Variables

Use a predictable precedence order:
1. explicit CLI flags
2. environment variables
3. config file
4. built-in defaults

Good practices:
- support `--config` or `--config-path`
- document relevant env vars in the README
- include `.env.example` when setup is non-trivial
- do not hardcode secrets
- avoid surprising config-file auto-discovery unless the rules are documented clearly

## Filesystem and Stream Handling

When the CLI touches files:
- accept explicit paths
- expand `~` when appropriate
- create parent directories only when expected and documented
- support `-` for stdin/stdout where it improves composability
- validate paths before expensive work begins

Useful conventions:
- input may default to stdin when omitted and sensible
- output may default to stdout unless a file path is requested
- `--output -` should explicitly mean stdout if both file and stream modes exist

## Safety Patterns

### Dry runs

For mutating commands, strongly consider `--dry-run`.

A good dry run:
- validates inputs
- shows intended changes
- avoids side effects
- follows the same execution path as the real command as much as possible

### Confirmation bypass

For destructive commands, require confirmation or an explicit `--yes`.

### Idempotence

If a command will be run by CI or automation, prefer idempotent behavior when possible.

Examples:
- repeatable setup commands should either succeed safely or report an already-correct state clearly
- config generation should not silently overwrite files without an explicit flag

## Testing Patterns

Test the CLI at two layers.

### 1) Business logic tests

Most behavior should be verifiable without invoking the CLI parser directly.

### 2) CLI integration tests

Test:
- argument parsing
- exit codes
- stdout/stderr separation
- error messages
- JSON/output-mode behavior
- dry-run behavior for mutating commands

Common approach:
- Typer/Click: `CliRunner`
- argparse: entrypoint-level tests or subprocess tests as appropriate

Minimum useful coverage:
- happy path
- invalid input
- missing files/config
- machine-readable mode
- a representative failure mode

## Documentation Expectations

A CLI-ready README should include:
- what the tool does
- install/run method
- primary commands
- important flags
- config/env requirements
- examples for both human and automation usage
- failure or exit semantics when relevant

If the CLI emits JSON or reads config files, document that explicitly.

## Included References

This skill ships with linked support files for concrete assets and examples:

- `references/greenfield-cli-checklist.md` — checklist for creating a new Python CLI
- `references/cli-structure.md` — opinionated project structure guidance
- `references/verification-playbook.md` — lightweight verification flow for CLI work
- `templates/pyproject.toml` — starter `pyproject.toml` for a Typer-based CLI
- `templates/cli.py` — thin Typer app template
- `templates/test_cli.py` — starter CLI test pattern

## Suggested External References

- Python Morsels articles: https://www.pythonmorsels.com/articles/browse/ — useful for idiomatic Python, iterable handling, refactoring patterns, and writing clearer CLI-supporting code

## Common Pitfalls

1. Putting business logic directly inside command callbacks.
2. Mixing logs, progress, and result data on stdout.
3. Returning `0` on failures because exceptions were swallowed.
4. Making human-readable output the only output mode for a tool that automation will use.
5. Adding too many nested subcommands when a flatter model would be clearer.
6. Using vague option names like `--value`, `--data`, or `--thing`.
7. Printing raw tracebacks for common user mistakes instead of actionable errors.
8. Writing fragile tests that ignore exit codes or stderr/stdout separation.
9. Coupling config discovery too tightly to one machine or one shell profile.
10. Breaking JSON mode with banners, color codes, or progress output.
11. Replacing an existing coherent repo convention with a different CLI framework without a strong reason.
12. Creating a new CLI package without wiring console scripts or documenting `uv` commands clearly.

## Verification Checklist

- [ ] Framework choice matches the repo and problem size
- [ ] Greenfield tools default to `uv` + `pyproject.toml` unless there is a good reason not to
- [ ] Command structure is shallow, consistent, and discoverable
- [ ] Business logic is separated from argument parsing and presentation
- [ ] Help text explains purpose, inputs, and important defaults
- [ ] stdout is safe for piping and stderr holds diagnostics
- [ ] Non-zero exit codes are returned on failures
- [ ] Machine-readable output exists when automation needs it
- [ ] Mutating commands consider `--dry-run`, `--yes`, or similar safeguards
- [ ] Config/env precedence is documented and predictable
- [ ] Tests cover happy path, invalid usage, and at least one real failure case
- [ ] Packaging and entrypoint setup match how users are expected to run the tool

## One-Shot Recipes

### Recipe: Turn a script into a maintainable CLI
1. Extract the script’s core behavior into plain Python functions.
2. Add a thin CLI layer with `typer` or `argparse`.
3. Move result data to stdout and diagnostics to stderr.
4. Add explicit exit codes and input validation.
5. Add tests for success, invalid input, and representative failure cases.

### Recipe: Add JSON mode to an existing CLI
1. Identify the canonical result object for the command.
2. Keep the result separate from presentation.
3. Add `--json` or `--format json`.
4. Ensure JSON mode writes only JSON to stdout.
5. Move logs, progress, and errors to stderr and update tests.

### Recipe: Make a destructive command safe
1. Add preflight validation.
2. Add `--dry-run` to preview changes.
3. Add `--yes` or explicit confirmation-bypass semantics.
4. Make overwrite behavior explicit with a dedicated flag.
5. Verify exit codes and user-facing error messages.

### Recipe: Create a greenfield Python CLI with the local preferred stack
1. Start from the `templates/pyproject.toml`, `templates/cli.py`, and `templates/test_cli.py` files in this skill.
2. Use `uv sync --dev` to realize the environment.
3. Keep CLI wiring thin and move real logic into reusable modules.
4. Add at least one happy-path test and one failure-path test.
5. Document install, run, and verification commands in the README.
