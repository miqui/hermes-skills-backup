---
name: golang-troubleshooting
description: "Use when debugging Go build failures, crashes, deadlocks, flaky tests, resource leaks, race conditions, slowdowns, or other unexpected behavior, with emphasis on reproduction, evidence gathering, and root-cause analysis before fixing."
version: 1.1.3
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, debugging, troubleshooting, delve, pprof, race-detector]
    related_skills: [systematic-debugging, golang-concurrency, golang-testing, golang-lint, code-performance-engineering]
---

# Go Troubleshooting

## Overview

This skill is the root-cause debugging guide for Go code. It is for situations where something is wrong: build failures, panics, flaky behavior, deadlocks, races, memory growth, latency spikes, or incorrect output.

The core rule is simple: **do not fix symptoms before you understand the cause**. Reproduce first, gather evidence, change one thing at a time, and verify the explanation before shipping a fix.

## When to Use

- A Go program crashes, hangs, leaks, or behaves incorrectly
- `go build`, `go test`, or runtime behavior does not match expectations
- A bug appears flaky, timing-dependent, or environment-dependent
- You need to escalate from print-debugging to the race detector, pprof, Delve, or runtime tracing
- You are auditing a Go codebase for common bug patterns and debugging risk

Do not use this skill as the primary reference for optimization patterns after the root cause is already known, or for broad non-Go debugging where a language-agnostic debugging skill is a better fit.

## Debugging Principles

1. **Read the error or symptom carefully first**
2. **Reproduce before fixing**
3. **Measure instead of guessing**
4. **Change one variable at a time**
5. **Trace the data flow to the root cause**
6. **Use the simplest tool that can reveal the next fact**
7. **Verify the fix and guard against regression**

## Quick Decision Tree

```text
WHAT ARE YOU SEEING?

"Build won't compile"
  → go build ./... ; go vet ./...
  → See references/compilation.md

"Wrong output / logic bug"
  → Write a failing test
  → See references/common-go-bugs.md and references/testing-debug.md

"Random crashes / panics"
  → GOTRACEBACK=all ./app ; go test -race ./...
  → See references/common-go-bugs.md and references/diagnostic-tools.md

"Sometimes works, sometimes fails"
  → go test -race ./...
  → See references/concurrency-debug.md and references/testing-debug.md

"Program hangs / frozen"
  → Inspect goroutine dumps / pprof goroutine profile
  → See references/concurrency-debug.md and references/pprof.md

"High CPU usage"
  → Capture CPU profile
  → See references/performance-debug.md and references/pprof.md

"Memory growing over time"
  → Capture heap profile
  → See references/performance-debug.md and references/concurrency-debug.md

"Slow / high latency / p99 spikes"
  → CPU + mutex + block profiles
  → See references/performance-debug.md and references/diagnostic-tools.md
```

## Golden Rules

### 1. Read the Error Message First

Go error messages and stack traces are usually precise. Start with:

- file and line numbers
- concrete type mismatches
- undefined names and import issues
- interface satisfaction failures
- panic stack traces and goroutine states

### 2. Reproduce Before You Fix

Always try to make the problem reproducible:

- write or isolate a failing test
- minimize the failing example
- remove nondeterminism where possible
- use `git bisect` if the regression origin is unclear

### 3. If You Do Not Measure It, You Are Guessing

Especially for performance and concurrency bugs:

- use `pprof` instead of intuition
- use the race detector instead of argument alone
- use repeated tests and benchmarks instead of single runs

### 4. One Hypothesis at a Time

If you change three things and the symptom moves, you still do not know why. Make one change, observe, then continue.

### 5. Research the Whole Code Path

A suspicious function in isolation may be safe because of caller guarantees, middleware, or input validation upstream. Trace the full path before declaring root cause.

### 6. Start Simple

Sometimes a focused log line or temporary print statement is the fastest path to the next fact. Escalate only when the simpler tool stops being informative.

## Red Flags

If any of these are happening, stop and reset the investigation:

- proposing a fix without explaining the cause
- making multiple speculative edits at once
- chasing symptoms that keep moving after each patch
- assuming the framework or compiler is wrong before checking your code
- saying “works on my machine” without identifying the environmental difference

## Escalation Guide

Start simple and escalate only as needed:

1. Reproduce with `go test`, `go build`, or a minimal command
2. Add targeted logging or a failing test
3. Run `go vet` and `golangci-lint`
4. Run `go test -race ./...` for suspected concurrency issues
5. Use `pprof` for CPU, heap, goroutine, mutex, or block investigation
6. Use Delve when you need live breakpoints, stepping, or state inspection
7. Use runtime tracing / `GODEBUG` when scheduler, GC, or runtime behavior is the question

## Reference Files

- [General Debugging Methodology](./references/methodology.md)
- [Common Go Bugs](./references/common-go-bugs.md)
- [Test-Driven Debugging](./references/testing-debug.md)
- [Concurrency Debugging](./references/concurrency-debug.md)
- [Performance Troubleshooting](./references/performance-debug.md)
- [pprof Reference](./references/pprof.md)
- [Diagnostic Tools](./references/diagnostic-tools.md)
- [Production Debugging](./references/production-debug.md)
- [Compilation Issues](./references/compilation.md)
- [Code Review Red Flags](./references/code-review-flags.md)

## Cross-References

- Use `golang-concurrency` when the problem is specifically about goroutines, channels, synchronization, or ownership patterns
- Use `golang-testing` when the next best step is building a stronger reproduction harness or test suite
- Use `golang-lint` when static analysis is likely to surface unchecked errors, suspicious constructs, or style-adjacent correctness issues
- Use `systematic-debugging` when the problem is broader than Go-specific tooling
- Use `code-performance-engineering` when Go slowdowns require broader benchmark design, Big-O analysis, before/after evidence, or language-agnostic optimization trade-off review in addition to pprof/runtime tooling

## Common Pitfalls

1. Fixing the symptom before understanding the cause
2. Treating flaky failures as unimportant because they are hard to reproduce
3. Skipping a failing test because the code “looks obvious”
4. Using advanced tools before simpler checks have narrowed the problem
5. Failing to verify that the fix actually eliminates the original class of bug

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The guidance centers root-cause analysis before fixes
- [ ] The escalation path goes from simple to advanced tools
- [ ] Cross-references point only to local skills
- [ ] The reference files still support the decision tree and workflow
