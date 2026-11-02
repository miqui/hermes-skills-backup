"""Minimal Python coding-agent starter.

What this shows:
- repo inspection tool contracts
- a tiny tool-dispatch loop
- targeted test execution
- structured tool results

This is a starter template, not a production-ready agent.
Recheck provider SDK methods and model names against current docs.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4.1"
REPO_ROOT = Path.cwd()


def _ok(data: dict[str, Any]) -> str:
    return json.dumps({"ok": True, **data})


def _err(message: str, **extra: Any) -> str:
    return json.dumps({"ok": False, "error": message, **extra})


def read_file(path: str) -> str:
    file_path = (REPO_ROOT / path).resolve()
    if not str(file_path).startswith(str(REPO_ROOT.resolve())):
        return _err("path escapes repo root", path=path)
    if not file_path.exists():
        return _err("file not found", path=path)
    return _ok({"path": path, "content": file_path.read_text(encoding="utf-8")})


def run_tests(scope: str = "") -> str:
    cmd = ["pytest"] + ([scope] if scope else [])
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return _ok(
        {
            "command": cmd,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )


def apply_patch(path: str, new_content: str) -> str:
    file_path = (REPO_ROOT / path).resolve()
    if not str(file_path).startswith(str(REPO_ROOT.resolve())):
        return _err("path escapes repo root", path=path)
    file_path.write_text(new_content, encoding="utf-8")
    return _ok({"path": path, "bytes_written": len(new_content.encode("utf-8"))})


def dispatch_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "read_file":
        return read_file(arguments["path"])
    if name == "run_tests":
        return run_tests(arguments.get("scope", ""))
    if name == "apply_patch":
        return apply_patch(arguments["path"], arguments["new_content"])
    return _err("unknown tool", tool=name)


def main() -> None:
    tools = [
        {
            "type": "function",
            "name": "read_file",
            "description": "Read a file from the repository.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "type": "function",
            "name": "run_tests",
            "description": "Run targeted pytest tests.",
            "parameters": {
                "type": "object",
                "properties": {"scope": {"type": "string"}},
            },
        },
        {
            "type": "function",
            "name": "apply_patch",
            "description": "Overwrite a file with new content after the model proposes a minimal safe fix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "new_content": {"type": "string"},
                },
                "required": ["path", "new_content"],
            },
        },
    ]

    user_task = "Fix the failing parser tests with the smallest safe patch. Read relevant files first, then run targeted tests."

    response = client.responses.create(model=MODEL, input=user_task, tools=tools)

    print("First model response:")
    print(response)
    print()
    print("Next step:")
    print("Inspect tool calls from the response, dispatch them with dispatch_tool(), then send tool results back in a follow-up response.")


if __name__ == "__main__":
    main()
