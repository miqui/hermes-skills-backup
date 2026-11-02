# Opinionated Python CLI Layout

Use this as a starting point for new Python CLI tools when the repo does not already define a different structure.

```text
project/
  cli/
    main.py
    commands/
      build.py
      inspect.py
  tests/
    test_cli_smoke.py
  pyproject.toml
  README.md
```

## Layout notes

- `cli/main.py` should construct the top-level app and register commands
- `commands/` should group command handlers by responsibility
- core business logic should live outside the command boundary when it needs isolated testing
- CLI modules should stay thin: parse arguments, call logic, format output

## Typer pattern

```python
import typer

app = typer.Typer()


@app.command()
def build(target: str, verbose: bool = False) -> None:
    ...


if __name__ == "__main__":
    app()
```

## Testing baseline

- one smoke test proving the CLI starts
- one command-level test for a common happy path
- add regression tests when fixing CLI bugs

## Common mistakes

- putting all logic directly inside command functions
- mixing display formatting and business logic too early
- making commands depend on hidden global state
- skipping help text or argument validation
