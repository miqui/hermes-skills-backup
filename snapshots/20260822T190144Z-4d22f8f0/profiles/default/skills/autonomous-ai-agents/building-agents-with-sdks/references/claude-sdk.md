# Claude / Anthropic SDK Reference

## Overview

Anthropic is a strong fit when you want a **custom coding-agent core** with explicit model turns, tool-use loops, and careful control over behavior.

For coding-agent work, think in three layers:

1. **Claude API + official SDKs** — the main programmable surface for custom coding agents.
2. **Claude Code** — Anthropic's coding-agent surface for repo-native workflows.
3. **MCP ecosystem** — a tool/resource integration layer that is highly relevant to repo-aware agents.

For most productized coding agents, the main starting point is the **Claude API plus official SDKs**.

## Best Fit

Choose Claude / Anthropic when:
- You want a strong direct-provider coding-agent implementation.
- You need explicit tool-use loops rather than a fully abstracted runtime.
- You are building debugging, patching, test-fixing, or review agents where reasoning quality matters.
- You want direct control over prompts, tool schemas, retries, and verification.

Less ideal when:
- You want a fully opinionated coding-agent runtime out of the box.
- You need a multi-provider routing layer more than a direct SDK.
- You want to avoid implementing your own loop and tool execution architecture.

## Core Primitives

The important primitives are:
- **messages / turns**
- **system instructions**
- **tool definitions**
- **tool use requests**
- **tool results**
- **streaming**
- **model selection**
- **usage accounting**

The core coding-agent pattern is:
1. Send coding task + tools.
2. Model responds with text and/or tool request.
3. Execute tool externally.
4. Return tool result.
5. Repeat until final patch or action plan.

This means the SDK is not the whole coding agent. You still own:
- repo access
- execution
- permissions
- retries
- state management
- verification

## Best Architecture Pattern

Use Claude SDKs when you want a **deliberate, inspectable coding loop**.

Recommended shape:
- model layer: Claude API
- repo layer: search/read/diff tools
- execution layer: test/lint/build commands
- edit layer: patch/write tools
- policy layer: approvals and restrictions
- verification layer: evidence-based success checks

This is especially strong for coding agents where you do not want hidden automation.

## Minimal Example Sketch

### Python coding-agent loop
```python
from anthropic import Anthropic

client = Anthropic()

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_tests(scope: str = "") -> str:
    import subprocess
    cmd = ["pytest"] + ([scope] if scope else [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return f"exit={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

tools = [
    {
        "name": "read_file",
        "description": "Read a source file from the repo",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "run_tests",
        "description": "Run targeted tests",
        "input_schema": {
            "type": "object",
            "properties": {"scope": {"type": "string"}}
        }
    }
]

resp = client.messages.create(
    model="claude-...",
    system="You are a careful coding agent. Read code, propose minimal fixes, and verify with tests.",
    messages=[
        {"role": "user", "content": "Fix the failing parser tests with the smallest safe patch."}
    ],
    tools=tools,
)
```

### TypeScript coding-agent loop
```ts
import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "fs";
import { execSync } from "child_process";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

function readFile(path: string): string {
  return readFileSync(path, "utf8");
}

function runTests(scope = ""): string {
  try {
    return execSync(scope ? `pytest ${scope}` : "pytest", { encoding: "utf8" });
  } catch (err: any) {
    return String(err.stdout || "") + "\n" + String(err.stderr || err.message || "");
  }
}

const response = await client.messages.create({
  model: "claude-...",
  system: "You are a careful coding agent. Make minimal edits and verify them.",
  messages: [
    { role: "user", content: "Investigate the failing auth tests and propose the smallest safe fix." }
  ],
  tools: [
    {
      name: "read_file",
      description: "Read a repo file",
      input_schema: {
        type: "object",
        properties: { path: { type: "string" } },
        required: ["path"]
      }
    },
    {
      name: "run_tests",
      description: "Run targeted tests",
      input_schema: {
        type: "object",
        properties: { scope: { type: "string" } }
      }
    }
  ]
});
```

### Implementation notes
- Start with read/search/test tools before allowing broad write access.
- Make the model produce a small hypothesis before editing.
- Verify every patch with targeted commands.
- Keep test output structured enough to feed back into the next turn.

## Common Pitfalls

1. **Treating the SDK like a complete runtime**
   You still need your own coding loop and guardrails.

2. **Poor tool schemas**
   Vague tool inputs lead to poor tool use.

3. **No verification layer**
   The model may say a file changed or tests passed without proof.

4. **Overly large tool surface area**
   Too many broad tools create unstable behavior.

5. **No summarization strategy**
   Context grows quickly in multi-step coding tasks.

6. **Confusing Claude Code with the low-level SDK path**
   Claude Code is adjacent and useful, but it is not the same architectural choice.

## Verification Checklist

- [ ] Confirm the current official SDK languages in Anthropic docs.
- [ ] Confirm the current package names and install commands.
- [ ] Recheck current tool-use examples and message formatting.
- [ ] Confirm any advanced features or beta surfaces before documenting them.
- [ ] Verify model names rather than hardcoding stale ones.
- [ ] Separate direct SDK guidance from Claude Code guidance.
- [ ] Verify your test-command wrapper and output parsing locally.

## Official Links

- Anthropic docs: https://docs.anthropic.com/
- API getting started: https://docs.anthropic.com/en/api/getting-started
- Python SDK: https://github.com/anthropics/anthropic-sdk-python
- TypeScript SDK: https://github.com/anthropics/anthropic-sdk-typescript
- MCP docs: https://modelcontextprotocol.io/

## Positioning Summary

Use Claude / Anthropic SDKs when you want to build a **careful custom coding agent** with explicit control over repo inspection, edit decisions, and verification.
