# OpenRouter Reference

## Overview

OpenRouter is best treated as a **model access and routing layer**, not as a full coding-agent SDK.

Its core value is simple:
- one API
- many models/providers
- OpenAI-compatible integration patterns for many existing stacks

For coding agents, that usually means OpenRouter sits **under** your repo loop, agent framework, or custom tool-execution layer.

## Best Fit

Choose OpenRouter when:
- You want quick access to many models through one interface.
- You already have an OpenAI-compatible coding-agent client or framework.
- You want model portability, routing, or fallback options.
- You want to experiment across providers without rewriting the coding-agent stack.

Less ideal when:
- You need a provider's newest or most specialized native features immediately.
- You want a full coding-agent platform with repo tools, memory, tracing, and orchestration built in.
- You need direct-provider guarantees for compliance, support, or feature parity.

## Core Primitives

The main concepts are:
- API key
- base URL
- model ID
- messages/prompts
- streaming
- tool/function calling where supported by the chosen model
- optional provider/routing configuration

The important architectural truth is:
**OpenRouter provides model access, not the coding-agent loop.**

## Best Architecture Pattern

Use OpenRouter underneath:
- a custom coding-agent loop
- an OpenAI-compatible coding framework
- a provider-agnostic evaluation stack

This works well when you want to swap models quickly or benchmark across providers.

Do not let the compatibility layer fool you into assuming universal feature parity. Always test the exact model/provider combination you ship.

## Minimal Example Sketch

### TypeScript coding-agent shape
```ts
import OpenAI from "openai";
import { readFileSync } from "fs";
import { execSync } from "child_process";

const client = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: "https://openrouter.ai/api/v1",
});

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

const resp = await client.chat.completions.create({
  model: "openai/gpt-4o-mini",
  messages: [
    { role: "system", content: "You are a careful coding agent. Make minimal fixes and verify them." },
    { role: "user", content: "Fix the failing parser tests with the smallest safe patch." }
  ],
  tools: [
    {
      type: "function",
      function: {
        name: "read_file",
        description: "Read a repo file",
        parameters: {
          type: "object",
          properties: { path: { type: "string" } },
          required: ["path"]
        }
      }
    }
  ]
});
```

### Python coding-agent shape
```python
from openai import OpenAI
import subprocess
from pathlib import Path

client = OpenAI(
    api_key="YOUR_OPENROUTER_KEY",
    base_url="https://openrouter.ai/api/v1",
)

def read_file(path: str) -> str:
    return Path(path).read_text()

def run_tests(scope: str = "") -> str:
    result = subprocess.run(["pytest", *([scope] if scope else [])], capture_output=True, text=True)
    return f"exit={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

resp = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a careful coding agent. Make minimal fixes and verify them."},
        {"role": "user", "content": "Investigate the failing auth tests and propose the smallest safe fix."}
    ],
)
```

### Implementation notes
- Build the repo loop once and swap only the model backend.
- Re-test prompts, tool calling, and output parsing on each target model.
- Treat model capability as provider/model specific, not OpenRouter-global.

## Common Pitfalls

1. **Assuming OpenAI-compatible means feature-identical**
   It does not.

2. **Skipping per-model capability tests**
   Tool calling, JSON output, context size, and latency all vary.

3. **Treating OpenRouter as the agent framework**
   You still need orchestration, repo tools, and verification elsewhere.

4. **Depending on output quirks from one model**
   Portability breaks quickly if prompts are too provider-specific.

5. **Not benchmarking direct-provider vs routed behavior**
   Routing convenience can come with tradeoffs.

## Verification Checklist

- [ ] Confirm the current base URL and auth pattern.
- [ ] Recheck current compatibility guidance in official docs.
- [ ] Verify routing/fallback options if your design depends on them.
- [ ] Check model support for tools, streaming, and structured outputs.
- [ ] Test the exact models you plan to use in production.
- [ ] Reconfirm any recommended attribution headers in current examples.
- [ ] Verify your repo/test wrapper behavior on each target model.

## Official Links

- Main site: https://openrouter.ai/
- Docs: https://openrouter.ai/docs
- Models catalog: https://openrouter.ai/models

## Positioning Summary

Use OpenRouter as a **portability and routing layer** beneath a coding-agent system. It is highly useful, but it is not the same thing as choosing the coding-agent architecture.
