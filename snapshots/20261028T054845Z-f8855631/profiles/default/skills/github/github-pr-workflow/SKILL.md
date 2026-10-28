---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.1.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review, local-git-workflow]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows a general GitHub workflow, with notes for environments that require a local wrapper skill instead of raw `git` or `gh` publication commands.

## Prerequisites

- Authenticated with GitHub (see `github-auth`)
- Inside a git repository with a GitHub remote

## Environment-Specific Wrapper Rule

If the active host requires a local wrapper for repository creation, pushes, branch publication, or pull-request creation, load and follow `local-git-workflow` instead of using the raw publication commands in this skill.

Use this skill for the PR lifecycle itself. Use `local-git-workflow` when a machine-specific wrapper policy controls how work is published.

### Quick Auth Detection

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` unless your local wrapper skill replaces it:

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description`
- `fix/description`
- `refactor/description`
- `docs/description`
- `ci/description`

## 2. Making Commits

Use Hermes file tools to edit, then commit:

```bash
git add src/auth.py src/models/user.py tests/test_auth.py

git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):

```text
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Preferred flow when a local wrapper skill is mandated

If the active environment requires a wrapper workflow, use `local-git-workflow` instead of the raw commands below.

### Push the Branch (generic flow)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number`.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
gh pr checks
gh pr checks --watch
```

**With git + curl:**

```bash
SHA=$(git rev-parse HEAD)

curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"
```

## 5. Updating a PR After Review

Make the requested changes, re-run relevant checks, then either:

- use `local-git-workflow` if the environment requires the wrapper, or
- use the normal `git push` flow on generic hosts

## 6. Merging

Use your repo's merge policy (merge commit, squash, or rebase). If the host requires a local wrapper for publication-side actions, defer to `local-git-workflow` where applicable.

## Related Skills

- Use `github-auth` for authentication setup
- Use `github-code-review` for review workflows and comments
- Use `local-git-workflow` when the current machine mandates wrapper-based publication instead of raw `git` or `gh`

## Common Pitfalls

1. Mixing generic GitHub PR guidance with host-specific wrapper requirements.
   If the active environment mandates wrapper-based publication, load `local-git-workflow` and follow it.

2. Opening a PR before pushing the correct branch.
3. Forgetting to watch CI after opening the PR.
4. Using inconsistent commit titles and PR titles.
5. Skipping branch sync and publishing stale diffs.

## Verification Checklist

- [ ] Branch and commit history reflect the intended change
- [ ] PR title/body communicate the actual change clearly
- [ ] CI status has been checked
- [ ] The merge path matches the repository policy
- [ ] `local-git-workflow` was used when the host required wrapper-based publication
