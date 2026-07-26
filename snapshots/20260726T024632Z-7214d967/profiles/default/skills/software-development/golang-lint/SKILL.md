---
name: golang-lint
description: "Use when configuring, running, or interpreting Go linters, especially golangci-lint, formatter integration, nolint suppressions, and code-quality enforcement for local development or CI."
version: 1.1.3
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, lint, golangci-lint, quality, static-analysis]
    related_skills: [golang-coding-style, golang-security, golang-testing, go-builder]
---

# Go Linting

## Overview

`golangci-lint` is the standard lint aggregation tool in most Go projects. It runs many linters behind a single CLI, supports shared configuration, and helps teams enforce correctness, readability, modernization, and test hygiene consistently.

This skill covers how to configure `golangci-lint`, run it effectively, interpret findings, decide when suppression is justified, and keep formatter and lint behavior aligned with team expectations.

## When to Use

- Setting up `golangci-lint` for a Go project
- Choosing which linters or formatters to enable
- Interpreting lint output and deciding whether to fix or suppress issues
- Adding or reviewing `.golangci.yml`
- Introducing linting incrementally in a legacy codebase
- Wiring lint checks into CI or pre-commit workflows

Do not use this skill as the primary reference for general Go style judgment, security design, or test strategy when a more specific skill is a better fit.

## Quick Reference

```bash
# Run all configured linters
golangci-lint run ./...

# Auto-fix issues where possible
golangci-lint run --fix ./...

# Run configured formatters
golangci-lint fmt ./...

# Run a single linter
golangci-lint run --enable-only govet ./...

# List available linters
golangci-lint linters

# Verbose output with timing info
golangci-lint run --verbose ./...
```

## Configuration

Every Go project that uses `golangci-lint` should keep its rules in `.golangci.yml` at the repo root. The bundled [recommended configuration](./assets/.golangci.yml) provides a production-oriented starting point with a broad set of correctness, style, testing, security, and modernization linters enabled.

For linter categories, what each linter checks, and configuration notes, see the [linter reference](./references/linter-reference.md).

## Suppressing Lint Warnings

Use `//nolint` directives sparingly. Fix the root cause first whenever practical.

```go
// Good: specific linter + justification
//nolint:errcheck // fire-and-forget logging, error is not actionable here
_ = logger.Sync()

// Bad: blanket suppression without reason
//nolint
_ = logger.Sync()
```

Rules:

1. `//nolint` directives SHOULD specify the linter name
2. `//nolint` directives SHOULD include a justification comment
3. `nolintlint` can enforce both rules automatically
4. Security-related suppressions deserve extra scrutiny

For patterns and examples, see [nolint directives](./references/nolint-directives.md).

## Development Workflow

1. Run linters after significant changes: `golangci-lint run ./...`
2. Auto-fix what you safely can: `golangci-lint run --fix ./...`
3. Run formatters before committing: `golangci-lint fmt ./...`
4. For large legacy codebases, adopt incrementally using `issues.new-from-rev`

Recommended Make targets:

```makefile
lint:
	golangci-lint run ./...

lint-fix:
	golangci-lint run --fix ./...

fmt:
	golangci-lint fmt ./...
```

For CI, run the same commands in automation rather than maintaining separate local and CI standards.

## Interpreting Output

Typical output format:

```text
path/to/file.go:42:10: message describing the issue (linter-name)
```

Use the linter name to decide what to do next:

- Look up the rule in the [linter reference](./references/linter-reference.md)
- Fix the issue if it points to a real bug, readability problem, or maintainability issue
- Suppress only when the code is intentionally correct and the rule does not fit the case
- Use `--verbose` when you need additional context or timing information

## Common Issues

| Problem | Solution |
| --- | --- |
| `deadline exceeded` | Increase `run.timeout` in `.golangci.yml` |
| Too many issues on legacy code | Use `issues.new-from-rev` to focus on changed code first |
| Linter not found | Check `golangci-lint linters` and upgrade if needed |
| Conflicting linter preferences | Disable the less valuable rule and document why |
| Old config format after an upgrade | Use `golangci-lint migrate` and re-check the config |
| Slow runs on large repos | Tune concurrency, exclusions, and enabled linters |

## Adopting Linting in Legacy Repos

Break cleanup into categories instead of fixing everything opportunistically:

- Auto-fixable issues first
- Then correctness and resource-safety issues
- Then style and maintainability findings
- Then higher-noise cleanup such as duplication or complexity reductions

Parallel review can help when your agent environment supports it, but the final lint policy should still be centralized in one configuration and one set of team conventions.

## Cross-References

- Use `golang-coding-style` for readability and style rules that depend on judgment beyond formatter output
- Use `golang-security` when lint findings overlap with security hardening or vulnerability prevention
- Use `golang-testing` when the findings are mostly test-specific and require testing-pattern guidance
- Use `go-builder` when linting is part of wider project setup or repo bootstrap work

## Common Pitfalls

1. Treating `golangci-lint` as a one-time cleanup tool instead of part of normal development
2. Enabling a large rule set without documenting which rules are mandatory vs. advisory
3. Using bare `//nolint` directives that hide intent
4. Keeping stale config comments that no longer match the actual enabled linters
5. Letting local runs and CI runs diverge over time

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The guidance matches the bundled `.golangci.yml` at a high level
- [ ] Cross-references point only to local skills
- [ ] The workflow guidance works for both local development and CI
