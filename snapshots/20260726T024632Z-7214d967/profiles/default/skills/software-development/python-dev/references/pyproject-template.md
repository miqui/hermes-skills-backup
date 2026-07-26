# pyproject.toml Template Notes

Use this as a starting point for new Python projects that use `uv`, `pytest`, `ruff`, and optionally `mypy`.

## Minimal structure

```toml
[project]
name = "your-project-name"
version = "0.1.0"
description = "Short project description"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
]

[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
  "pytest>=8.0.0",
  "ruff>=0.6.0",
  "mypy>=1.11.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
```

## Notes

- Keep `requires-python` explicit
- Put runtime dependencies in `[project].dependencies`
- Put developer-only tools in `[dependency-groups].dev`
- Include `[build-system]` when the repo uses a `src/` layout or is meant to be installed by `uv sync`; without it, `uv` may install dependencies but not the project itself, so `src/` never gets added through an editable install
- Only enable stricter `mypy` rules if they match the repo’s maturity level
- If the repo already uses other tool sections, extend them instead of duplicating settings

## Typical commands

```bash
uv sync
uv run pytest
uvx ruff check .
uv run mypy .
```

## Common mistakes

- leaving dependency versions completely unconstrained in brand-new projects
- adding tools but not configuring them at all
- omitting `[build-system]` in a `src/` layout and then assuming `uv sync` installed the project package
- splitting truth across `requirements.txt`, `setup.py`, and `pyproject.toml` without a reason
- enabling strict typing rules that the current repo cannot realistically satisfy
