# Codex auth debugging

Use this when Codex is installed but `codex exec` fails with 401s.

## Observed symptom

A real failure mode on macOS:

- `codex exec 'Reply with exactly READY and nothing else.'`
- output shows provider `openai`
- websocket and HTTPS calls fail with:
  - `401 Unauthorized`
  - `Missing bearer or basic authentication in header`

This can happen even when `OPENAI_API_KEY` exists in a dotenv file.

## Fast triage

1. Verify Codex is installed:
   - `command -v codex`
   - `codex --version`
2. Verify the key is actually valid with OpenAI, independent of Codex.
3. Verify export behavior, not just shell-local variable presence:
   - `set -a; source ~/.hermes/.env; set +a`
   - `env | grep '^OPENAI_API_KEY='`
4. Re-test Codex in a temp git repo:
   - `TMP=$(mktemp -d) && cd "$TMP" && git init && codex exec 'Reply with exactly READY and nothing else.'`
5. If the key is valid and exported but Codex still fails, inspect:
   - `codex login --help`
   - `codex login status`

## Important distinction

A direct OpenAI API check can succeed while Codex still fails. That usually narrows the issue to Codex auth handling rather than key validity.

## Recovery paths

- Preferred when allowed: `printenv OPENAI_API_KEY | codex login --with-api-key`
- If the user does not want Codex to store credentials locally, stop after documenting that env-only auth is not working for this installation and report partial setup.

## User-facing conclusion template

- Codex installed: yes/no
- API key stored in Hermes env: yes/no
- Direct OpenAI API validation: pass/fail
- Standalone Codex working end-to-end: yes/no
- If no: note whether the blocker is unexported env vs Codex-local login requirement
