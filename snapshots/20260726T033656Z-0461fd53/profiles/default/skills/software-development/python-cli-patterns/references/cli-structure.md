# Opinionated Python CLI Structure

Use this as a starting point for new Python CLI tools when the repository does not already define a better structure.

```text
project/
  pyproject.toml
  README.md
  src/mytool/
    __init__.py
    cli.py
    main.py
    core/
      __init__.py
      operations.py
  tests/
    test_cli.py
    test_core.py
```

## Layout notes

- `src/mytool/cli.py` should define the Typer app and command functions
- `src/mytool/main.py` can provide a tiny executable bridge if needed
- `src/mytool/core/` should hold reusable logic independent of the CLI framework
- tests should cover both the CLI surface and underlying logic

## Recommended file responsibilities

### `cli.py`
- define the app
- declare commands/options/arguments
- map expected failures to clean user-facing errors
- keep command functions thin

### `core/operations.py`
- implement actual behavior
- accept ordinary Python parameters
- return ordinary Python values
- remain easy to test without invoking the CLI

### `main.py`
- provide a minimal launch path if the package also supports `python -m mytool`

## Good boundaries

Good pattern:
- parse in CLI layer
- execute in core layer
- present in CLI layer

Bad pattern:
- parse, validate, perform I/O, catch errors, format output, and implement business rules all inside one command function

## Example shape

```python
# src/mytool/cli.py
import json
import typer

from mytool.core.operations import inspect_value

app = typer.Typer(help="Inspect values and print results.")


@app.command()
def inspect(name: str, json_output: bool = typer.Option(False, "--json")) -> None:
    result = inspect_value(name)
    if json_output:
        typer.echo(json.dumps(result))
        return
    typer.echo(f"name={result['name']} status={result['status']}")
```

```python
# src/mytool/core/operations.py
def inspect_value(name: str) -> dict[str, str]:
    return {"name": name, "status": "ok"}
```
