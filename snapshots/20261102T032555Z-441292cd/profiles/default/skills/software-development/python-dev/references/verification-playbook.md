# Python Verification Playbook

Use the lightest verification that meaningfully proves the change.

## Recommended order

1. Focused test for the changed behavior
2. Broader test file or package
3. Lint or type checks if configured
4. Smoke test if no formal tests exist

## Common commands

```bash
uv run pytest tests/test_specific_file.py
uv run pytest
uvx ruff check .
uv run mypy .
python -m pytest
```

## What to report back

- which commands were run
- whether they passed or failed
- any checks you could not run
- remaining risks or unverified areas

## Common mistakes

- declaring success after edits without running checks
- running only the full suite when a fast focused test would catch the issue sooner
- changing project tooling and forgetting to update docs or config
- ignoring failing baseline tests without calling them out
