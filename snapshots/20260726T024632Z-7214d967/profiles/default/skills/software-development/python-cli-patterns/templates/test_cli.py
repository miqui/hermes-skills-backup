from typer.testing import CliRunner

from mytool.cli import app

runner = CliRunner()


def test_inspect_happy_path() -> None:
    result = runner.invoke(app, ["inspect", "sample"])
    assert result.exit_code == 0
    assert "name=sample status=ok" in result.stdout


def test_inspect_json_mode() -> None:
    result = runner.invoke(app, ["inspect", "sample", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '{"name": "sample", "status": "ok"}'


def test_inspect_empty_name_is_usage_error() -> None:
    result = runner.invoke(app, ["inspect", "   "])
    assert result.exit_code == 2
    assert "Error: name must not be empty" in result.stderr
