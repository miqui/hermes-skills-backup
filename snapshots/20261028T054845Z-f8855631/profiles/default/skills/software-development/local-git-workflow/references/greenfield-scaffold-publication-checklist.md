# Greenfield scaffold publication checklist

Use this when publishing a newly scaffolded local app or service from this machine with `/Users/miqui/development/scripts/git-workflow.sh`.

## When this reference helps

- You created a new local repo from a generated scaffold (Vite, Node, Python, etc.)
- You ran verification steps before first publish
- The project produces build artifacts or generated local data that should not be committed
- You want the smallest safe path from scaffold -> verified local repo -> GitHub repo

## Recommended sequence

1. Create the project under `/Users/miqui/development/<repo-name>`.
2. Initialize the local repo first:

```bash
git init -b main
```

3. Add or confirm ignore rules for generated outputs before publication. Typical examples:
   - `node_modules/`
   - `dist/`
   - `coverage/`
   - `*.tsbuildinfo`
   - generated local data files under `public/data/` or similar
4. Run the local verification you need before first publish, for example:
   - dependency install
   - data generation
   - build/test/lint
5. Inspect the index and working tree carefully:

```bash
git status --short --branch
```

6. If the repo contains mixed staged and unstaged changes, explicitly stage the intended allowlist so generated or ignored-adjacent files are not accidentally omitted.
7. Publish with the wrapper:

```bash
bash /Users/miqui/development/scripts/git-workflow.sh init "feat: initial project scaffold"
```

8. If the user wants repo metadata, set it after publication without bypassing the wrapper for push/PR flow:

```bash
gh repo edit <owner>/<repo> --description "..."
```

9. Verify final remote state:

```bash
git status --short --branch
git remote -v
```

## Why this exists

Greenfield app scaffolds often create local-only generated outputs during verification. The main failure mode is not wrapper failure; it is publishing a noisy first commit because ignore rules and `git status` were not checked before `init`.

## Practical example classes

- Vite/React/TypeScript app with `dist/` and `*.tsbuildinfo`
- local corpus/index generators that write to `public/data/`
- Dockerized local preview apps that build before first push
