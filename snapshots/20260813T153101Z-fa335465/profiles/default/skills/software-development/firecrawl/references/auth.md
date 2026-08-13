# Firecrawl Auth and API-Key Flow

Use this reference when a human must authorize Firecrawl in the browser or when an agent needs to obtain a Firecrawl API key without assuming one already exists.

## When to Use

- `FIRECRAWL_API_KEY` is missing
- the user needs to sign up or sign in first
- the agent needs to hand a browser-auth URL to a human and then poll for completion
- the install command was run with `--browser` but key availability still needs verification

## First Check

Before repeating auth, verify whether a valid key is already available in the working environment or project config.

- If `FIRECRAWL_API_KEY` already exists and is valid, skip this flow.
- If the install command was run with `--browser`, the human may already have completed sign-in.

## Human Browser Entry Point

If a human just needs the sign-in or sign-up page:

- `https://www.firecrawl.dev/signin?view=signup&source=agent-suggested`

## Agent-Assisted CLI Auth Flow

### Step 1 — Generate auth parameters

```bash
SESSION_ID=$(openssl rand -hex 32)
CODE_VERIFIER=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n' | head -c 43)
CODE_CHALLENGE=$(printf '%s' "$CODE_VERIFIER" | openssl dgst -sha256 -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
```

### Step 2 — Ask the human to open the auth URL

```text
https://www.firecrawl.dev/cli-auth?code_challenge=$CODE_CHALLENGE&source=coding-agent#session_id=$SESSION_ID
```

If the human already has a Firecrawl account, they sign in and authorize.
If not, they create an account first and then authorize.

### Step 3 — Poll for completion

```http
POST https://www.firecrawl.dev/api/auth/cli/status
Content-Type: application/json

{"session_id": "$SESSION_ID", "code_verifier": "$CODE_VERIFIER"}
```

Poll every 3 seconds.

Possible responses:

- `{"status": "pending"}`
- `{"status": "complete", "apiKey": "fc-...", "teamName": "..."}`

### Step 4 — Save the key

```bash
echo "FIRECRAWL_API_KEY=fc-..." >> .env
```

Prefer the project-local `.env` or the environment configuration mechanism already used by the target codebase.

## Important Distinction

This browser flow is different from:

- `https://www.firecrawl.dev/auth.md`

Use `auth.md` only when the agent platform can mint a WorkOS ID-JAG identity assertion and exchange it directly at `/agent/auth`.

## Pitfalls

1. Re-running auth without first checking whether a valid key already exists.
2. Saving the key in the wrong `.env` or wrong project context.
3. Confusing browser auth for human authorization with the separate `auth.md` agent-assertion flow.
4. Polling the status endpoint without preserving the original `SESSION_ID` and `CODE_VERIFIER` pair.
