# OWASP API Security Top 10 — lifecycle governance overlay

This reference maps OWASP API security concerns into the APIOps Cycles lifecycle used by the `api-governance` skill. The goal is not to bolt security on at the end, but to apply security governance where decisions are made.

## How to use this reference

- Use it as a **governance overlay**, not a replacement for product, platform, or design review.
- Apply the relevant risks at the lifecycle stage where they are easiest to prevent.
- Revisit risks across stages: many issues begin in strategy or design and only become visible in delivery or operations.

## OWASP API Top 10 themes to govern

Use the canonical OWASP list/version your organization adopts. Across versions, the recurring governance themes are:
- Broken object-level authorization (BOLA)
- Broken authentication
- Broken object property level authorization / excessive data exposure / mass assignment
- Unrestricted resource consumption
- Broken function-level authorization
- Unrestricted access to sensitive business flows
- Server-side request forgery (SSRF)
- Security misconfiguration
- Improper inventory management
- Unsafe consumption of APIs

## Lifecycle mapping

### 1. API Product Strategy

**Security governance intent:** prevent launching the wrong trust model.

Focus on:
- Identify the API audience and exposure model: internal, partner, public, regulated
- Classify business sensitivity, abuse potential, and fraud risk
- Determine whether the API enables sensitive business flows requiring stronger review
- Decide early what trust assumptions are invalid

Key prompts:
- Could misuse of this capability create financial, privacy, or operational harm?
- Are there privileged flows that need stricter controls than ordinary CRUD?
- Is this API consuming or brokering untrusted downstream APIs?

Common OWASP themes surfaced here:
- unrestricted access to sensitive business flows
- unsafe consumption of APIs
- improper inventory management

### 2. API Consumer Experience

**Security governance intent:** make secure usage the default consumer path.

Focus on:
- Authentication and authorization expectations in onboarding
- Safe defaults in examples and quickstarts
- Developer guidance on scopes, tokens, errors, retries, and limits

Key prompts:
- Will consumers understand how to use least-privilege credentials?
- Do examples accidentally normalize insecure usage patterns?
- Are auth failures and permission boundaries clear?

Common OWASP themes surfaced here:
- broken authentication
- broken function-level authorization
- unrestricted resource consumption

### 3. API Platform Architecture

**Security governance intent:** establish secure platform boundaries before implementation.

Focus on:
- Network boundaries, service-to-service trust, egress controls, secret handling
- Gateway controls, policy enforcement points, and centralized authn/authz patterns
- Tenant isolation, data segmentation, and dependency trust decisions

Key prompts:
- Where are the enforcement points for identity, policy, throttling, and logging?
- Could this architecture enable SSRF or unsafe outbound calls?
- Are inventory, ownership, and runtime visibility defined?

Common OWASP themes surfaced here:
- SSRF
- security misconfiguration
- improper inventory management
- unsafe consumption of APIs

### 4. API Design

**Security governance intent:** encode secure behavior into the contract and interaction model.

Focus on:
- Resource- and field-level authorization model
- Input and output data minimization
- Sensitive operations, role boundaries, and workflow protections
- Pagination, filtering, query limits, and anti-abuse constraints

Key prompts:
- Can consumers access only the objects they are allowed to access?
- Can consumers write only the fields they are allowed to change?
- Does the contract overexpose data by default?
- Are expensive operations bounded?

Common OWASP themes surfaced here:
- BOLA
- broken function-level authorization
- broken object property level authorization / excessive data exposure / mass assignment
- unrestricted resource consumption

### 5. API Delivery

**Security governance intent:** verify the implementation matches the secure design.

Focus on:
- AuthN/AuthZ test coverage
- Negative testing for role boundaries and data exposure
- Dependency review and safe outbound call handling
- Secure defaults in deployment and infrastructure automation

Key prompts:
- Do automated tests prove denial paths as well as allow paths?
- Are rate limits, egress rules, and config baselines applied in real environments?
- Are secrets, debug flags, and admin surfaces controlled?

Common OWASP themes surfaced here:
- broken authentication
- security misconfiguration
- SSRF
- unsafe consumption of APIs

### 6. API Audit

**Security governance intent:** determine whether unresolved security risk blocks release.

Focus on:
- Review open security findings, accepted risks, and compensating controls
- Check inventory, ownership, and operational accountability
- Ensure security exceptions are explicit and time-bounded

Key prompts:
- Which OWASP-relevant risks remain open?
- Are compensating controls real, documented, and monitored?
- Is the API’s exposure level consistent with its actual controls?

### 7. API Publishing

**Security governance intent:** publish with controlled exposure and clear expectations.

Focus on:
- Correct audience targeting and access issuance
- Documentation that does not leak sensitive internals
- Clear deprecation, support, and incident contact paths

Key prompts:
- Is the API being exposed more broadly than its controls justify?
- Are docs/examples free of insecure patterns or secrets?
- Is inventory updated so the API is discoverable to operators and governors?

Common OWASP themes surfaced here:
- improper inventory management
- security misconfiguration
- broken authentication

### 8. Monitoring and Improvements

**Security governance intent:** detect drift, abuse, and broken assumptions after launch.

Focus on:
- Auth failures, authorization denials, unusual object access patterns
- Resource exhaustion, scraping, or automated abuse trends
- New downstream trust or SSRF indicators
- Recurring config drift or shadow API discovery

Key prompts:
- What security signals would indicate abuse or broken policy?
- How are suspicious access patterns investigated?
- How do findings feed back into design and platform standards?

Common OWASP themes surfaced here:
- unrestricted resource consumption
- improper inventory management
- broken authorization/authentication patterns
- security misconfiguration

## Minimum security governance checks by stage

- **Strategy:** classify sensitivity, exposure model, abuse potential, business-flow risk
- **Consumer Experience:** define safe onboarding, credential model, scopes, and usage guidance
- **Architecture:** define trust boundaries, policy enforcement points, inventory, and egress controls
- **Design:** define object/field/function authorization, data minimization, and anti-abuse limits
- **Delivery:** automate tests for authn/authz, configuration baselines, and negative cases
- **Audit:** review unresolved risks, exceptions, and monitoring readiness
- **Publishing:** confirm access model, docs hygiene, and inventory registration
- **Monitoring:** watch for abuse, drift, misconfiguration, and anomalous access patterns

## Important reminder

OWASP concerns should be mapped into lifecycle checkpoints, not treated as a single security appendix. If security is reviewed only at audit time, governance is too late.