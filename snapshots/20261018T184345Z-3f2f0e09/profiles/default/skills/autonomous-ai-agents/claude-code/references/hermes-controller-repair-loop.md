# Hermes controller repair loop for Claude Code print-mode tasks

Use this when Hermes is orchestrating and Claude Code is the coding lane for a small or medium implementation task.

## Pattern

1. Write a short task contract into repo-local context files such as `README.md` and `CLAUDE.md`.
2. Run a bounded first pass with `claude -p ... --max-turns N`.
3. If Claude exits with `Reached max turns`, do **not** discard the run.
   - inspect `git status --porcelain=v1`
   - inspect the key files Claude created or changed
   - decide whether the work is complete enough to verify directly or needs a narrower follow-up prompt
4. Verify outside Claude with real commands.
   - prefer one targeted test first
   - then run the broader suite
5. If verification fails, send Claude the **exact failing command and traceback/output** and ask for the smallest fix that makes the suite pass.
6. Re-run verification independently before reporting success.

## Why this matters

This gives Hermes a visible control loop:
- Claude writes code
- Hermes verifies outcomes
- failures become precise follow-up inputs instead of vague re-prompts

That is a better interview/demo story than pretending the first pass must be perfect.

## Shell-safe prompting for repair turns

When a repair prompt includes tracebacks, markdown fences, or inline backticks, avoid pasting the whole transcript directly inside a double-quoted shell string. Backticks inside the prompt can be interpreted by the shell before `claude -p` runs.

Safer pattern:

```bash
cat >/tmp/claude-repair-prompt.txt <<'EOF'
Fix only the issues needed to make the test suite pass.

Exact failure:
from app.main import app
ModuleNotFoundError: No module named 'app'
EOF

claude -p "$(cat /tmp/claude-repair-prompt.txt)" --allowedTools "Read,Edit,Write,Bash" --max-turns 8
```

If you already have a prompt string in memory, another safe option is to remove markdown backticks and keep the quoted failure transcript plain-text.

## Good follow-up prompt shape

- state that the implementation is close
- include the exact failure
- ask for the smallest fix
- ask Claude to run the tests after the fix
- request a final summary of the fix and verification
