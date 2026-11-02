---
name: hsb-skill-pr-delivery
description: Use when adding skills to hermes-skills-backup via PRs.
---

# Delivering skills to hermes-skills-backup

Use with parallel agents: layout, stacking and shared-checkout pitfalls.

## Layout
- Repo stores skills only as full snapshots: `snapshots/<id>/profiles/default/skills/<category>/<skill>/SKILL.md`. No top-level `skills/` dir; do not invent one.
- Cloud skills go under `iac/cloud/<provider>/` (e.g. `iac/cloud/gcp/`) in ONE existing snapshot.
- Regenerate MANIFEST.json, RESTORE.md, skills-corpus.json with `hsb-snapshot` after each skill. It aborts on pre-existing placeholder secret warnings, so run `betterleaks dir <skill dir>` first, then use `--no-secrets-check`. `hsb-validate`/`hsb-verify` must pass.

## Parallel-agent rules
- Never share one checkout: `git-workflow.sh change` stages everything, so stray files (even 100MB `.terraform` binaries) get swept into other agents' branches. One dedicated worktree per agent.
- Parallel PRs touching the same snapshot conflict on manifest files. Author SKILL.md files in scratch in parallel (no git), then ONE integrator lands them as a stacked series (each branch cut from the previous); merge in order.
- Decide layout BEFORE dispatching wave 1; mixed layouts cost a full consolidation pass.
- Add `.terraform/`, `*.tfstate*` to .gitignore.
- Validate HCL extracted from the exact SKILL.md text (fmt -check, init -backend=false, validate); retyped copies drift and need variable declarations.
- Subagents' `git branch -D` / `rm -rf` hit approval blocks; ask Miguel to approve or clean up himself.
- Mark gcloud/CLI commands UNVERIFIED unless run against a real project.
- Doc-authoring children: tell them to fetch with web_extract/web_search directly; child execute_code/terminal calls hit approval prompts that get withdrawn and fail the task (needs re-dispatch). Integrator children running git/hsb shell steps hit the same block: have Miguel approve promptly or run those steps in the parent.
- Child shell approvals time out (approvals.timeout, default 60s) and are withdrawn if nobody answers in Slack. Inline interpreters (`python -c`, heredocs, `perl -e`, `execute_code`) ALWAYS prompt, so tell integrators: edit with patch/write_file, run only plain commands (git, hsb-*, betterleaks, gh, git-workflow.sh), and rely on `hsb-validate` for frontmatter checks. Durable fix: add those commands to `command_allowlist` in config.yaml (edit via terminal, not the patch tool) and/or raise approvals.timeout.
- Integrator children make partial progress then stop: when re-dispatching, name the existing worktree/branch/snapshot id so it resumes instead of recreating.
- Drop secondary-source (blog) citations from drafts before integrating into one PR.
- `git-workflow.sh change` creates its own new timestamped branch even if a local branch exists; the pre-made branch is left unused.
- `hsb-restore` from the primary checkout can abort integrity checks on untracked files in a snapshot dir; restore from the worktree's snapshot instead.
- Miguel (Vercel skills batch): do not run/verify Vercel CLI commands for now; leave them UNVERIFIED.
