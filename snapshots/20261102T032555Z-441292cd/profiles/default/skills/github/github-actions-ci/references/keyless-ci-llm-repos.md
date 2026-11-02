# Keyless CI for repos with LLM-touching Python scripts

Validated 2026-09-08 building `miqui/AI-evals` (Braintrust LLM-as-judge topic,
Python 3.12). Pattern: the repo's eval/example scripts call real model APIs,
but CI has no credentials by design — the user runs LLM-backed scripts
locally with keys exported as env vars (e.g. `ANTHROPIC_API_KEY`,
`BRAINTRUST_API_KEY`). CI covers lint + deterministic smoke tests only.

## Why clients fail at import, not at call time

The OpenAI and Anthropic Python SDKs raise (e.g. `OpenAIError: Missing
credentials`) the moment the client object is *constructed* with no key env
var — module-level `client = OpenAI()` / `client = Anthropic()` in an eval
script fails at import, long before any network call. Any smoke test that
imports the scripts under test therefore fails in a keyless CI environment
even though the scripts themselves are correct.

## The pattern

1. **Tests, not CI, own the dummy credentials.** In the pytest file, an
   autouse fixture sets dummy values via `monkeypatch.setenv` (e.g.
   `ANTHROPIC_API_KEY: test-dummy-key-not-real`). Construction succeeds; no
   request is made at import time because the scripts only call the client
   inside `task()` / `__main__` blocks.
2. **The workflow pins keys to empty strings.** In the test job's `env:`, set
   every provider key to `""` (e.g. `ANTHROPIC_API_KEY: ""`). Combined with
   (1) this documents and enforces that no test path can reach a real
   provider even if a secret leaks into the runner.
3. **Smoke tests stay deterministic.** Test only what runs without a model:
   module imports succeed, pure code scorers (exact match), constant tables
   (choice-score maps). Never assert on LLM output in CI.
4. **Match the CI Python version locally.** The host may lack the CI version
   (e.g. only 3.14/3.11/3.9 installed while CI targets 3.12). Provision the
   exact version with `uv venv --python 3.12 .venv` so local verification
   equals CI verification before publishing.
5. **Version-floor deps against PyPI reality, not docs.** Braintrust docs
   examples suggested `autoevals>=0.16.0`, but PyPI's actual latest is 0.3.0.
   A docs-transcribed version floor makes `uv pip install -e .` unresolvable.
   Resolve real versions with uv/pip before committing the floor.

## Resolved workflow shape (AI-evals ci.yml)

- Triggers: `pull_request` (Miguel's standing rule: validation on every PR) +
  `workflow_dispatch`; `concurrency` group canceling in-progress runs.
- Two jobs: `lint` (ruff check + ruff format --check) and `smoke` (pytest,
  empty-string provider keys). Both: `actions/setup-python` with
  `cache: pip`, `pip install -e '.[dev]'`.

## Known deviation to fix on next PR

The published `ci.yml` used tag refs (`actions/checkout@v4`,
`actions/setup-python@v5`), not the full-SHA pins this skill mandates in
section 3. Pin both actions to full commit SHAs with version comments in the
repo's first feature PR (`ci:` conventional title), before adding more jobs.
