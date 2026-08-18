/* Minimal TypeScript coding-agent starter.
 *
 * What this shows:
 * - repo inspection tool contracts
 * - targeted test execution
 * - structured tool results
 *
 * This is a starter template, not a production-ready agent.
 * Recheck SDK methods and model names against current docs.
 */

import OpenAI from "openai";
import { execFileSync } from "child_process";
import { existsSync, readFileSync, writeFileSync } from "fs";
import path from "path";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const MODEL = "gpt-4.1";
const REPO_ROOT = process.cwd();

type ToolResult = {
  ok: boolean;
  error?: string;
  [key: string]: unknown;
};

function safePath(relativePath: string): string {
  const full = path.resolve(REPO_ROOT, relativePath);
  if (!full.startsWith(path.resolve(REPO_ROOT))) {
    throw new Error(`Path escapes repo root: ${relativePath}`);
  }
  return full;
}

function readFileTool(filePath: string): ToolResult {
  try {
    const full = safePath(filePath);
    if (!existsSync(full)) return { ok: false, error: "file not found", path: filePath };
    return { ok: true, path: filePath, content: readFileSync(full, "utf8") };
  } catch (error) {
    return { ok: false, error: String(error), path: filePath };
  }
}

function runTestsTool(scope = ""): ToolResult {
  try {
    const args = scope ? [scope] : [];
    const stdout = execFileSync("pytest", args, { cwd: REPO_ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    return { ok: true, command: ["pytest", ...args], exit_code: 0, stdout, stderr: "" };
  } catch (error: any) {
    return {
      ok: true,
      command: ["pytest", ...(scope ? [scope] : [])],
      exit_code: error.status ?? 1,
      stdout: String(error.stdout || ""),
      stderr: String(error.stderr || error.message || ""),
    };
  }
}

function applyPatchTool(filePath: string, newContent: string): ToolResult {
  try {
    const full = safePath(filePath);
    writeFileSync(full, newContent, "utf8");
    return { ok: true, path: filePath, bytes_written: Buffer.byteLength(newContent, "utf8") };
  } catch (error) {
    return { ok: false, error: String(error), path: filePath };
  }
}

function dispatchTool(name: string, args: Record<string, unknown>): ToolResult {
  if (name === "read_file") return readFileTool(String(args.path));
  if (name === "run_tests") return runTestsTool(String(args.scope || ""));
  if (name === "apply_patch") return applyPatchTool(String(args.path), String(args.new_content));
  return { ok: false, error: `unknown tool: ${name}` };
}

async function main() {
  const tools = [
    {
      type: "function",
      name: "read_file",
      description: "Read a file from the repository.",
      parameters: {
        type: "object",
        properties: { path: { type: "string" } },
        required: ["path"],
      },
    },
    {
      type: "function",
      name: "run_tests",
      description: "Run targeted pytest tests.",
      parameters: {
        type: "object",
        properties: { scope: { type: "string" } },
      },
    },
    {
      type: "function",
      name: "apply_patch",
      description: "Overwrite a file with new content after the model proposes a minimal safe fix.",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string" },
          new_content: { type: "string" },
        },
        required: ["path", "new_content"],
      },
    },
  ];

  const response = await client.responses.create({
    model: MODEL,
    input: "Fix the failing parser tests with the smallest safe patch. Read relevant files first, then run targeted tests.",
    tools,
  });

  console.log("First model response:");
  console.dir(response, { depth: null });
  console.log("\nNext step: inspect tool calls, dispatch with dispatchTool(), then send tool results back in a follow-up response.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
