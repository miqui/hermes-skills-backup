# OpenHands-Orchestrated Domain Monitor Pattern

Use this when the user wants an AI-agent-style project for an operational workflow, but the core task is deterministic and safety-sensitive.

## Best-fit shape

- Local app owns the business logic
- OpenHands owns orchestration/runtime behavior
- A scheduled or on-demand command produces a machine-readable report
- OpenHands reads the report and communicates the result

## Recommended repository layout

```text
repo/
├── README.md
├── .env.example
├── pyproject.toml
├── scripts/
│   └── run_check.sh
├── openhands/
│   ├── system_prompt.md
│   ├── task_template.md
│   └── allowed_actions.md
├── src/<app>/
│   ├── config.py
│   ├── models.py
│   ├── service.py
│   ├── guardrails.py
│   ├── state.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── mock.py
│   │   └── live_provider.py
│   └── notifier/
│       └── emailer.py
└── tests/
```

## Why this works

OpenHands is strongest as a runtime that can:
- run repo commands
- inspect files and outputs
- apply policy
- summarize results
- supervise retries

It is usually weaker than deterministic code for:
- provider normalization
- threshold logic
- cooldown/deduping
- safety-sensitive allow/deny enforcement

## Guardrail checklist

Use multiple layers:

1. Prompt-level policy
   - explicit allowed and forbidden actions
2. Repo-level code guardrails
   - reject forbidden operations by action name
3. Tool/capability limits
   - do not expose purchase-capable or destructive tools unless necessary
4. Secret scoping
   - do not provide credentials that would enable forbidden actions

## Mock-first recommendation

If the live provider is uncertain:
- create a `mock` provider that returns normalized sample data
- verify the full decision and notification loop with tests
- add the live provider as a stub with a clear note to validate against official docs before implementation

## Example fit

- airfare price watcher with email-only alerts
- stock/market threshold watcher
- job posting monitor
- product price-drop notifier
- uptime or error digest agent

## Verification

At minimum:
- lint the repo
- test config validation
- test the rule engine
- test guardrails
- test dedupe/cooldown behavior
- run one smoke check with the mock provider
