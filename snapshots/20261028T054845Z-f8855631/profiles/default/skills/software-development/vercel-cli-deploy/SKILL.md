---
name: vercel-cli-deploy
description: Use when deploying to Vercel from a terminal or CI. Covers CLI install/login/link, preview vs production, prebuilt deploys, env pull, promote/rollback, logs, vercel.json, GitHub Actions.
version: 1.0.0
tags: [vercel, cli, deploy, ci-cd, github-actions, devops]
---

# Vercel CLI and Deploy Workflow

Source: official Vercel docs only (see Sources). Commands marked UNVERIFIED were taken from docs and not run in this session; nothing here was executed.

## 1. Install, update, authenticate

```bash
npm i -g vercel            # or: pnpm i -g vercel | yarn global add vercel | bun add -g vercel
vercel --version
npm i -g vercel@latest     # update (UNVERIFIED)
vercel login               # interactive (UNVERIFIED)
vercel whoami              # confirm identity (UNVERIFIED)
```

- Non-interactive/CI: create a token at https://vercel.com/account/tokens and export `VERCEL_TOKEN`.
- Prefer the `VERCEL_TOKEN` env var over `--token=...`: args can leak in process lists/logs. If both are set, `--token` wins.
- Never print or commit tokens; use `<VERCEL_TOKEN>` placeholders in docs/scripts.

## 2. Link a local directory to a project

```bash
vercel link                # prompts for scope + project (UNVERIFIED)
```

- Creates `.vercel/` holding `project.json` with `orgId` and `projectId`. Add `.vercel` to `.gitignore`.
- Running `vercel` / `vercel --prod` in an unlinked dir also links it (docs: "Initial Deployment").
- Team scope: global options `--scope <team-slug>` / `--team`.
- Monorepo: run from repo root with `--cwd <path>` or set Root Directory in project settings.

## 3. Local development

```bash
vercel dev                 # replicate Vercel env locally (UNVERIFIED)
vercel env pull .env.local # write Development env vars to a file
```

- `vercel env pull [file]` exports Development vars; re-run after any change to env vars (dashboard, `vercel env add`, `vercel env rm`). Existing target files are merged, local-only entries kept.
- `vercel env run -- <command>` runs a command with project env injected, without writing a file.
- If the framework has its own dev server (`next dev`), `vercel dev` is often unnecessary; use `env pull` + framework dev.

## 4. Preview vs production deploys

```bash
vercel                     # = vercel deploy → Preview deployment
vercel deploy --prod       # Production deployment
vercel --cwd ./apps/web    # deploy a subdirectory project
```

- stdout is ALWAYS the deployment URL; logs/progress go to stderr. Capture: `url=$(vercel deploy --token "$VERCEL_TOKEN")` — in CI prefer env var form.
- Exit code ≠ 0 means failure; inspect stderr.
- Verify a preview before promoting:
  ```bash
  vercel curl / --deployment <preview-url>
  vercel logs --deployment <deployment-id> --level error   # flag shown in overview docs
  ```
- `vercel deploy --temporary` gives an unauthenticated, claimable deployment; not available in CI or in an already-linked dir.
- Useful: `--dry` (single-file), `--guidance` (suggest next steps), `--yes`, `--non-interactive`.
- Git-connected projects deploy automatically on push (PR = preview, production branch = production). CLI deploys work with or without Git.

## 5. Prebuilt deploys (build locally/CI, upload output)

```bash
vercel pull --yes --environment=preview --token "$VERCEL_TOKEN"      # or --environment=production
vercel build                      # add --prod when targeting production
vercel deploy --prebuilt          # add --prod for production
```

- `vercel pull` fetches project settings + env vars into `.vercel/`; `vercel build` writes `.vercel/output` (Build Output API); `--prebuilt` uploads that output.
- Environment used in `pull` and `build`/`deploy` must match: production needs `--environment=production`, `vercel build --prod`, `vercel deploy --prebuilt --prod`.
- `--prebuilt` requires a directory deploy (not single-file).

## 6. Promote, rollback, redeploy

```bash
vercel promote <deployment-id-or-url> [--timeout=5m]   # make deployment current production
vercel promote status [project]
vercel rollback [<deployment-id-or-url>]               # revert production
vercel rollback status [project]
```

- Promoting a Preview deployment asks for confirmation and creates a new production deployment; `--yes` skips the prompt.
- Default promote timeout `3m`; a timeout does not cancel the promotion; `--timeout=0` returns immediately.
- Hobby plan: rollback only to the previous production deployment; older targets need Pro.
- Undo a rollback with `vercel promote <deployment>` (also re-enables auto-assignment of production domains). Rollbacks stop auto-assigning new production deploys to domains until you promote.
- See also `vercel redeploy`, `vercel remove`, `vercel list`, `vercel alias` (all UNVERIFIED here).

## 7. Logs and inspection

```bash
vercel logs                                       # last 100 runtime records, last 30 min, linked project
vercel logs --deployment <dpl_id|url>
vercel logs --environment production
vercel logs runtime --query 'level:error AND timeout'
vercel logs requests --query 'httpStatus >= 500'  # CDN request records
vercel inspect <deployment-url>                   # UNVERIFIED
```

- Describes CLI v64.0.0+; older versions had different options. History depth depends on plan.
- `--project/-p` defaults to the linked project. Build logs: dashboard or `vercel inspect --logs` (UNVERIFIED).

## 8. Project settings and vercel.json

- Dashboard Project Settings sets framework preset, Build/Install/Output commands, Root Directory, Node version, env vars, domains.
- File config in repo overrides defaults: `vercel.json` or `vercel.toml` (static), or `vercel.ts` (programmatic). Only ONE config file per project.
- Minimal example:
  ```json
  {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "buildCommand": "npm run build",
    "outputDirectory": "dist",
    "installCommand": "npm ci",
    "redirects": [{ "source": "/old", "destination": "/new", "permanent": true }],
    "headers": [{ "source": "/(.*)", "headers": [{ "key": "X-Frame-Options", "value": "DENY" }] }]
  }
  ```
  (Property names UNVERIFIED against the full reference; check https://vercel.com/docs/project-configuration.)
- Env vars: `vercel env ls | add <name> [environment] | rm <name>` (UNVERIFIED); each scoped to development/preview/production (or custom env).

## 9. CI/CD with GitHub Actions

Use Actions only when you need tests, scans, perf budgets, or approval gates; Vercel's Git integration already makes previews and rollbacks. Otherwise you build twice.

Secrets (GitHub repo → Settings → Secrets): `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`. IDs come from `.vercel/project.json` after `vercel link`. Reference as `${{ secrets.* }}`; never hardcode.

```yaml
name: Vercel Production Deployment
env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
  VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
on:
  push:
    branches: [main]
jobs:
  Deploy-Production:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install --global vercel@latest
      - run: vercel pull --yes --environment=production
      - run: vercel build --prod
      - run: vercel deploy --prebuilt --prod
```

- Preview workflow: `branches-ignore: [main]`, `--environment=preview`, no `--prod`.
- Tag-triggered production: `on.push.tags: ['*']`.
- Multiple projects: separate secrets e.g. `VERCEL_PROJECT_ID_APP`, `VERCEL_PROJECT_ID_DOCS`.
- Trade-offs: building in Actions loses Vercel's managed build cache and automatic PR comments; post preview URL yourself. Monorepos: Turborepo remote cache (`TURBO_TOKEN`, `TURBO_TEAM`); `actions/setup-node@v4` `cache` for deps.
- Vercel can trigger Actions via `deployment_status` / `repository_dispatch` for E2E on live previews.
- (Workflow above adapted from the KB pattern; UNVERIFIED by execution.)

## Pitfalls / common build failures

- **Missing creds in CI**: "No existing credentials" / prompts hang → set `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`; add `--yes`/`--non-interactive`.
- **Env mismatch**: `pull` for preview but `deploy --prod` (or vice versa) ships wrong vars. Keep all three steps on the same environment.
- **`--prebuilt` without build**: needs `.vercel/output` from `vercel build`. Also, System Environment Variables (e.g. `VERCEL_URL`, `VERCEL_GIT_*`) are absent at build time with `--prebuilt`; frameworks relying on them may break — then don't use `--prebuilt`.
- **Building twice**: running `vercel deploy` without `--prebuilt` after a CI build makes Vercel rebuild.
- **Wrong output dir / build command**: "No Output Directory found" → set Output Directory/Build Command in settings or `vercel.json`.
- **Wrong Root Directory in monorepos**: set Root Directory or `--cwd`; ensure "include files outside root" if needed.
- **Dependency/lockfile or Node version mismatch**: pin Node version in project settings and commit the lockfile; private deps need a token in env vars.
- **Env var missing at build**: it must exist for the target environment; re-run `vercel env pull` locally after changes.
- **Committed `.vercel/` or tokens**: add `.vercel` to `.gitignore`; rotate any leaked token.
- **Two config files**: only one of vercel.json / vercel.toml / vercel.ts.
- **Stale CLI**: older CLIs differ (e.g. `vercel logs` pre-v64). Update to latest.
- **Rollback surprises**: after rollback, new deploys don't auto-assign to production domains until you `vercel promote`.
- **Hidden/ignored files**: `.vercelignore` excludes files from uploads; single-file deploys refuse ignored files.

## Sources (fetched 2026-10-28)

- https://vercel.com/docs/cli
- https://vercel.com/docs/cli/deploy
- https://vercel.com/docs/cli/promote
- https://vercel.com/docs/cli/rollback
- https://vercel.com/docs/cli/env
- https://vercel.com/docs/cli/logs
- https://vercel.com/docs/deployments/overview
- https://vercel.com/docs/project-configuration
- https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel (official Vercel KB)
