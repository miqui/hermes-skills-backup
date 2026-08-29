---
name: golang-security
description: "Use when writing, reviewing, or auditing Go code for security issues, especially around trust boundaries, injection, cryptography, filesystem access, secrets, authentication, and dependency or tooling-based vulnerability checks."
version: 1.1.5
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, security, secure-coding, vulnerability-review, auth]
    related_skills: [golang-lint, golang-troubleshooting, api-governance, go-builder]
---

# Go Security

## Overview

This skill is for security-oriented work in Go codebases: secure code review, vulnerability prevention, threat modeling, security-sensitive implementation choices, and validation with static or dependency-analysis tools.

The emphasis is on **defense in depth**: validate inputs at trust boundaries, choose secure defaults, minimize blast radius, and assume that a single layer of defense can fail.

## When to Use

- Reviewing Go code for vulnerabilities or risky patterns
- Writing or modifying code that handles user input, secrets, cookies, files, auth, crypto, or external commands
- Auditing a service for common web, injection, or data-exposure risks
- Checking a Go repo with security tooling such as `gosec` or `govulncheck`
- Deciding how to reduce risk at trust boundaries and sensitive operations

Do not use this skill as the only reference for broader system security architecture, compliance programs, or non-Go-specific threat modeling where a wider security process is needed.

## Security Thinking Model

Before writing or reviewing code, ask:

1. **Where are the trust boundaries?**
2. **What inputs can an attacker influence?**
3. **Which operations are sensitive if those inputs are wrong?**
4. **What is the blast radius if a defense fails?**
5. **What independent layer would still reduce harm?**

## Severity and Prioritization

Use severity to prioritize remediation, not to avoid investigation.

| Level | Meaning |
| --- | --- |
| Critical | Remote code execution, full credential theft, auth bypass, severe data breach |
| High | Significant data exposure, broken crypto, dangerous injection, privilege escalation |
| Medium | Defense weakening, partial information disclosure, weaker session handling |
| Low | Best-practice deviations with limited direct impact |

Threat-modeling guidance and DREAD examples live in [references/threat-modeling.md](./references/threat-modeling.md).

## Research Before Reporting

Do not judge a snippet in isolation if the codebase can tell you more.

1. Trace the data to its origin
2. Check upstream validation, parsing, allow-lists, and middleware
3. Check the real trust boundary involved
4. Confirm whether downstream code assumes an invariant that is actually enforced
5. Adjust severity when defenses exist, but do not pretend the finding disappears

Document why a finding is safe, downgraded, or still dangerous. A short comment with the reasoning is often better than leaving the decision implicit.

## Threat Modeling

Use STRIDE at trust-boundary crossings and sensitive data flows:

- **Spoofing** — identity and session claims
- **Tampering** — integrity of requests, files, or stored data
- **Repudiation** — missing or untrustworthy audit trails
- **Information Disclosure** — secrets, PII, tokens, internal state
- **Denial of Service** — unbounded input, expensive work, no rate limits, resource leaks
- **Elevation of Privilege** — bypassing authorization or isolation boundaries

For fuller methodology, see [references/threat-modeling.md](./references/threat-modeling.md).

## Quick Reference

| Risk | Typical failure | Preferred defense |
| --- | --- | --- |
| SQL injection | Building SQL with concatenated input | Parameterized queries |
| Command injection | Passing untrusted input through shell parsing | Use `exec.Command` with separate args |
| XSS / unsafe HTML | Rendering attacker-controlled HTML/JS | Prefer `html/template` and safe output rules |
| Path traversal | Joining user-controlled paths to sensitive roots | Restrict to a root and validate cleaned paths |
| Weak crypto choices | Deprecated or unauthenticated algorithms | Use vetted library primitives and secure defaults |
| Secret leakage | Hardcoded credentials or unsafe logs | Use secret managers/env vars and sanitize logs |
| Timing leaks | Direct equality on secrets | Use constant-time comparison where relevant |
| Resource exhaustion | Missing limits/timeouts/rate limits | Bound work, add timeouts, rate-limit sensitive endpoints |
| Concurrency bugs with security impact | Races around auth/session/shared state | Avoid unsafe shared state; test with `-race` |

## Detailed Categories

For examples and detailed guidance, see:

- [Cryptography](./references/cryptography.md)
- [Injection Vulnerabilities](./references/injection.md)
- [Filesystem Security](./references/filesystem.md)
- [Network/Web Security](./references/network.md)
- [Cookie Security](./references/cookies.md)
- [Third-Party Data Leaks](./references/third-party.md)
- [Memory Safety](./references/memory-safety.md)
- [Secrets Management](./references/secrets.md)
- [Logging Security](./references/logging.md)
- [Threat Modeling Guide](./references/threat-modeling.md)
- [Security Architecture](./references/architecture.md)
- [Security Review Checklist](./references/checklist.md)

## Tooling and Verification

### Static Analysis

Security-relevant linters often include `bodyclose`, `sqlclosecheck`, `errcheck`, `govet`, `staticcheck`, and related rules from your `golangci-lint` config. Use the local `golang-lint` skill for lint policy and configuration guidance.

For deeper security-focused analysis:

```bash
# SAST scanner
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...

# Vulnerable dependency and call-path scanner
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

### Security Testing

```bash
# Race detector
go test -race ./...

# Fuzz testing
go test -fuzz=Fuzz
```

Use tooling as evidence, not as a substitute for reasoning. A clean run does not prove the design is safe.

## Common Mistakes

| Severity | Mistake | Why it is risky | Fix |
| --- | --- | --- | --- |
| High | `math/rand` for tokens | Predictable output | Use `crypto/rand` |
| Critical | SQL string concatenation | Attacker controls query structure | Use placeholders / parameterization |
| Critical | `exec.Command("bash", "-c", userInput)` | Shell interprets attacker input | Pass explicit arguments, avoid shell parsing |
| Critical | Hardcoded secrets | Secrets leak into history, CI, and backups | Move to env vars or a secret manager |
| Medium | Secret comparison with `==` | Can leak timing information | Use constant-time comparison when needed |
| Medium | Returning overly detailed internal errors | Helps attackers map internals | Return generic client errors, log details safely |
| High | Ignoring `-race` findings in auth/session logic | Data races can become correctness or auth bugs | Fix races before trusting the code path |
| High | Using weak password hashing or obsolete algorithms | Cheap to brute-force or unsafe by design | Use Argon2id or bcrypt for password storage |
| High | Using unauthenticated encryption modes casually | Ciphertext can be modified undetected | Prefer authenticated encryption modes |

## Security Anti-Patterns

| Anti-pattern | Why it fails | Better approach |
| --- | --- | --- |
| Security through obscurity | Hidden endpoints and conventions are discoverable | Enforce authentication and authorization |
| Trusting client-provided identity headers | Clients can forge them | Verify identity server-side |
| Client-side-only authorization | Any HTTP client can bypass UI checks | Enforce authorization on the server |
| Shared secrets across environments | One breach spreads everywhere | Separate secrets per environment |
| Ignoring crypto errors | Silent failure becomes insecure behavior | Fail closed and handle errors explicitly |
| Rolling your own crypto | Easy to get subtly wrong | Use vetted library primitives and standard patterns |

## Cross-References

- Use `golang-lint` for lint and static-analysis configuration that supports secure coding
- Use `golang-troubleshooting` when a security issue is manifesting as a runtime failure, race, leak, or hard-to-reproduce bug
- Use `api-governance` when the security question is really about API policy, lifecycle controls, or review gates
- Use `go-builder` when the work includes wider service setup, dependency management, or project bootstrap decisions

## Additional Resources

- [Go Security Best Practices](https://go.dev/doc/security/best-practices)
- [gosec](https://github.com/securego/gosec)
- [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
- [OWASP Go Secure Coding Practices](https://owasp.org/www-project-go-secure-coding-practices-guide/)

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The skill focuses on trust boundaries and defense in depth
- [ ] The guidance uses tools as evidence, not as a substitute for reasoning
- [ ] Cross-references point only to local skills
- [ ] The reference docs still cover the main security domains mentioned here
