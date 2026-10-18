# Greenfield Python CLI Checklist

Use this checklist when creating a new Python CLI from scratch.

## Foundation

- [ ] Pick a clear command name
- [ ] Decide whether the package name and CLI command name should differ
- [ ] Create a `src/` layout for reusable/distributable tools
- [ ] Use `pyproject.toml` as the single source of truth
- [ ] Prefer Python `>=3.11`
- [ ] Use `uv` for environment sync and command execution

## CLI framework and shape

- [ ] Default to `typer` unless stdlib-only or repo constraints point to `argparse`
- [ ] Keep the command tree shallow and predictable
- [ ] Choose whether the tool is single-purpose, resource+verb, or action-oriented
- [ ] Define flags and positionals for readability, not cleverness
- [ ] Add `--help` descriptions that explain purpose and defaults

## Output and behavior

- [ ] Decide what goes to stdout vs stderr
- [ ] Add `--json` or `--format` if automation will consume output
- [ ] Define non-zero failure behavior
- [ ] Consider `--verbose`, `--quiet`, and `--debug`
- [ ] For mutating commands, consider `--dry-run` and `--yes`

## Code structure

- [ ] Keep CLI wiring thin
- [ ] Put business logic in reusable functions/modules
- [ ] Keep parsing, I/O, and domain logic separated
- [ ] Add typed function signatures for new code

## Testing and verification

- [ ] Add at least one happy-path CLI test
- [ ] Add at least one invalid-usage or failure-path test
- [ ] Verify stdout/stderr separation where it matters
- [ ] Run `uv run pytest`
- [ ] Run `uvx ruff check .`
- [ ] Run `uv run mypy .` when the project uses mypy

## Packaging and docs

- [ ] Add a console-script entry point
- [ ] Document install/run commands in `README.md`
- [ ] Document config/env variables
- [ ] Document JSON mode or file conventions if present
- [ ] Document any destructive or side-effecting behavior explicitly
