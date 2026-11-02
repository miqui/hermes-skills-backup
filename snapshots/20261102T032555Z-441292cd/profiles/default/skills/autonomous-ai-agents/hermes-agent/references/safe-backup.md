# Safe Hermes backup / restore

Use this when the goal is disaster recovery for a Hermes install **without leaking secrets**.

## Recommended backup set

Back up only these classes of files from `$HERMES_HOME`:

- `memories/MEMORY.md`
- `memories/USER.md`
- `SOUL.md`
- `skills/`
- `config.yaml` after sanitizing any key/token/secret/password fields
- `shell-hooks-allowlist.json` if present

## Explicit exclusions

Do not include:

- `.env`
- `auth.json`
- `sessions/`
- `logs/`
- `state.db`, `state.db-wal`, `state.db-shm`
- `gateway_state.json`
- `channel_directory.json`
- `state-snapshots/`
- `cache/`
- `__pycache__/`, `.git/`, lockfiles, virtualenvs

## Practical repo workflow

For a Git-backed backup repo, keep:
- tracked sanitized state in a stable directory like `snapshot/`
- timestamped local archives in a gitignored directory like `backup-output/`

This lets the user review diffs before push while keeping historical local snapshots.

## Restore sequence

1. Reinstall Hermes.
2. Restore `config.yaml`, `memories/`, `skills/`, `SOUL.md`, and optional shell-hook allowlist.
3. Recreate secrets manually:
   - `.env`
   - `auth.json` or provider logins
   - `gh auth login`
   - `hermes login`
   - platform credentials/tokens
4. Run:
   - `hermes config check`
   - `hermes doctor`

## GitHub push pitfalls

### `gh repo create --source . --push` on a brand-new repo

This fails if the local repo has no commit yet. Safer sequence:

```bash
git init
git add .
git commit -m "feat: initial safe hermes backup toolkit"
git branch -M main
gh repo create <owner>/<repo> --private --source . --remote origin
git push -u origin main
```

### SSH host key verification on first push

If the repo remote is `git@github.com:...` and the machine has never trusted GitHub's host key, first push may fail with:

```text
Host key verification failed.
```

Initialize trust first:

```bash
mkdir -p ~/.ssh
ssh-keyscan github.com >> ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts
```

Or run `ssh -T git@github.com` interactively once.
