import json

import typer

app = typer.Typer(help="Example Python CLI.")


class UsageError(Exception):
    pass


def inspect_value(name: str) -> dict[str, str]:
    cleaned = name.strip()
    if not cleaned:
        raise UsageError("name must not be empty")
    return {"name": cleaned, "status": "ok"}


@app.command()
def inspect(
    name: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
) -> None:
    try:
        result = inspect_value(name)
    except UsageError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2)

    if json_output:
        typer.echo(json.dumps(result))
        return

    typer.echo(f"name={result['name']} status={result['status']}")


if __name__ == "__main__":
    app()
