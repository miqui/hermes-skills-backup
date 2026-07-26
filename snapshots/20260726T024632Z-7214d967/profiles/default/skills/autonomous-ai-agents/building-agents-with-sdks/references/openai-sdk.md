# OpenAI SDK Reference

## Overview

OpenAI is a strong choice when you want a broad official surface for coding-agent development, from low-level model/tool loops up to higher-level agent abstractions.

The practical layers are:

1. **Responses API + official SDKs** — the core low-level foundation for custom coding agents.
2. **Agents SDK** — a higher-level orchestration layer for tool-using and multi-step agents.
3. **Realtime API** — usually secondary for coding agents, but relevant for live pair-programming or voice-assisted development.
4. **Legacy surfaces** like Chat Completions or Assistants — relevant mainly for existing systems or migration work.

For new coding-agent systems, the strongest default is usually **Responses API first**, then move up to the Agents SDK if it reduces boilerplate without taking away necessary control.

## Best Fit

Choose OpenAI when:
- You want a well-supported mainstream SDK path for coding agents.
- You need strong tool use, structured outputs, or higher-level orchestration.
- You want the option to start low-level and later adopt an agent SDK.
- You expect to build bug-fixing, refactoring, or repo-review agents with clear tool boundaries.

Less ideal when:
- You want a ready-made coding-agent runtime rather than a product-embedded SDK.
- You want portability across many model providers more than a direct provider SDK.

## Core Primitives

### Responses API
The key primitives are:
- input
- model
- tools
- structured output / schemas
- response output items
- streaming
- iterative follow-up with tool results

### Agents SDK
Typical abstractions include:
- agent
- runner / run loop
- tools
- handoffs
- guardrails / validation
- tracing / observability
- session/state helpers

### Realtime API
Key concepts include:
- session
- event stream
- text/audio input and output
- tool calls during a live session

## Best Architecture Pattern

If you are building a coding-agent product:
- start with Responses API if you need explicit control
- move to Agents SDK when you want less loop boilerplate
- keep repo access, execution, verification, and policy outside the model abstraction

If you are building a live pair-programming agent:
- add Realtime only if live streaming or voice actually matters
- otherwise keep the first version simpler

## Minimal Example Sketch

### Python Responses API coding-agent loop
```python
from openai import OpenAI
import subprocess
from pathlib import Path

client = OpenAI()

def read_file(path: str) -> str:
    return Path(path).read_text()

def run_tests(scope: str = "") -> str:
    cmd = ["pytest"] + ([scope] if scope else [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return f"exit={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

tools = [{
    "type": "function",
    "name": "read_file",
    "description": "Read a source file from the repo",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"]
    }
}, {
    "type": "function",
    "name": "run_tests",
    "description": "Run targeted tests",
    "parameters": {
        "type": "object",
        "properties": {"scope": {"type": "string"}}
    }
}]

resp = client.responses.create(
    model="gpt-4.1",
    input="Fix the failing serializer tests with the smallest safe patch.",
    tools=tools,
)
```

### TypeScript Responses API coding-agent loop
```ts
import OpenAI from "openai";
import { readFileSync } from "fs";
import { execSync } from "child_process";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

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

const resp = await client.responses.create({
  model: "gpt-4.1",
  input: "Investigate the failing login tests and propose the smallest safe fix.",
  tools: [
    {
      type: "function",
      name: "read_file",
      description: "Read a repo file",
      parameters: {
        type: "object",
        properties: { path: { type: "string" } },
        required: ["path"]
      }
    },
    {
      type: "function",
      name: "run_tests",
      description: "Run targeted tests",
      parameters: {
        type: "object",
        properties: { scope: { type: "string" } }
      }
    }
  ]
});
```

### Python Agents SDK sketch
```python
# Pseudocode shape; recheck exact imports in current docs.
from agents import Agent, Runner, tool
import subprocess
from pathlib import Path

@tool
def read_file(path: str) -> str:
    return Path(path).read_text()

@tool
def run_tests(scope: str = "") -> str:
    result = subprocess.run(["pytest", *([scope] if scope else [])], capture_output=True, text=True)
    return f"exit={result.returncode}\n{result.stdout}\n{result.stderr}"

agent = Agent(
    name="bug-fixer",
    instructions="You are a careful coding agent. Read code, propose minimal edits, and verify them.",
    tools=[read_file, run_tests],
)

result = Runner.run(agent, "Fix the failing parser tests with the smallest safe patch.")
print(result.final_output)
```

### Implementation notes
- Use structured tool contracts and keep command wrappers narrow.
- Separate repo search/read from edit application and from verification.
- Keep the first loop focused on one failure class, not whole-repo autonomy.

## Common Pitfalls

1. **Assuming tool calls execute automatically**
   The application must still execute tools.

2. **Skipping validation**
   Model-generated tool arguments must be checked.

3. **Not bounding the loop**
   Add iteration, time, and retry limits.

4. **Mixing low-level and high-level layers carelessly**
   Choose a clear boundary between Responses API and Agents SDK use.

5. **Using legacy examples as defaults for new systems**
   Old examples can distort the architecture.

6. **Assuming every model supports every feature equally**
   Tool calling, structured outputs, and realtime behavior vary.

## Verification Checklist

- [ ] Confirm the current recommended API surface for new agents.
- [ ] Confirm the current SDK language support.
- [ ] Recheck the current Agents SDK package names and examples.
- [ ] Verify how tool results should be sent back in current docs.
- [ ] Confirm model support for the exact capabilities you need.
- [ ] Recheck Realtime specifics before documenting implementation details.
- [ ] Verify the repo/test command wrappers locally.

## Official Links

- OpenAI docs: https://platform.openai.com/docs
- Responses API: https://platform.openai.com/docs/api-reference/responses
- Function calling guide: https://platform.openai.com/docs/guides/function-calling
- Realtime guide: https://platform.openai.com/docs/guides/realtime
- Python SDK: https://github.com/openai/openai-python
- Node SDK: https://github.com/openai/openai-node

## Positioning Summary

Use OpenAI SDKs when you want a **broad official coding-agent surface** with a path from low-level control to higher-level orchestration.
