# Python CLI Verification Playbook

Use the lightest verification that meaningfully proves the CLI change.

## Recommended order

1. Focused CLI test for the changed behavior
2. Broader test file or package
3. Lint and type checks if configured
4. Smoke test if no formal tests exist

## Common commands

```bash
uv run pytest tests/test_cli.py
uv run pytest
uvx ruff check .
uv run mypy .
uv run python -m mytool --help
```

## What to verify

- exit codes
- stdout/stderr separation
- help output for touched commands
- JSON or machine-readable output modes
- failure-path behavior for representative errors

## What to report back

- which commands were run
- whether they passed or failed
- which checks could not be run
- remaining risks or unverified areas

## Common mistakes

- declaring success after code edits without running checks
- testing only core logic and not the CLI surface
- checking output text but not exit codes
- forgetting to test JSON mode or stderr behavior
- ignoring failing baseline tests without calling them out
