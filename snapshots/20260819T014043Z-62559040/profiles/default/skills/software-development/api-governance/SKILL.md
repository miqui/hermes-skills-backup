---
name: api-governance
description: "Use when planning, designing, reviewing, or evolving APIs that need governance across the full lifecycle, using APIOps Cycles as the primary backbone for decisions, checkpoints, and quality gates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [api, governance, apiops, lifecycle, design, review, audit, platform]
    related_skills: [writing-plans, openapi-api-designer, openapi-specification, graphql-api, node-backend, requesting-code-review, application-authorization]
---

# API Governance

## Overview

Use this skill to keep API governance active across the entire API lifecycle rather than treating governance as a one-time review near launch. The governing backbone is **APIOps Cycles**, especially the **New API** flow:

1. API Product Strategy
2. API Consumer Experience
3. API Platform Architecture
4. API Design
5. API Delivery
6. API Audit
7. API Publishing
8. Monitoring and Improvements

The core idea is simple: **governance is continuous decision-making plus evidence**, not just approval. At each stage, define what must be true, how it will be checked, who needs to be aligned, and what artifacts prove readiness.

This skill is intentionally opinionated about lifecycle governance first. It can later be extended with specific enterprise style guides, security baselines such as the OWASP API Top 10, regulatory requirements, and organization-specific platform policies. For OpenAPI contract design, pair with `openapi-api-designer`; for OpenAPI 3.2+ specification mechanics, validation, and migration review, pair with `openapi-specification`; for GraphQL schema contracts, resolver boundaries, query cost controls, and schema evolution, pair with `graphql-api`; for authorization model design (RBAC/ABAC/ReBAC), role/permission lifecycle governance, and policy enforcement point architecture, pair with `application-authorization`.

## Linked References

- `references/apiops-cycles.md` — source summary and lifecycle mapping from APIOps Cycles: New API
- `references/owasp-api-top-10.md` — OWASP API security concerns mapped into lifecycle governance stages
- `references/lifecycle-stage-control-mapping.md` — stage-to-control matrix for governance objectives, evidence, and stakeholders
- `references/style-guides.md` — API style-guide overlay mapped across lifecycle governance stages
- `templates/api-governance-review.md` — reusable review template for lifecycle-based API governance

## When to Use

- Designing a new API product or internal service API
- Reviewing whether an API is ready to move from idea to implementation or publication
- Defining governance checkpoints for API teams, platform teams, architects, or security reviewers
- Creating API lifecycle standards, review templates, or quality gates
- Auditing an existing API initiative to see where governance is missing
- Writing plans or decision records for API-first delivery

Don't use for:
- Pure endpoint-by-endpoint coding tasks with no governance, lifecycle, or platform questions
- Narrow framework implementation details that are better handled by language- or stack-specific skills
- Security-only reviews when the task is strictly exploit analysis rather than governance and lifecycle quality

## Core Governance Principles

1. **Govern throughout the lifecycle**
   Governance starts before interface design and continues after release.

2. **Govern outcomes, not only documents**
   Look for evidence that teams understand users, risks, architecture, operations, and change management.

3. **Prefer reusable standards over one-off exceptions**
   If a decision recurs, turn it into a standard, checklist item, or reusable template.

4. **Shift feedback left**
   Pull consumer, platform, security, and operational concerns earlier in the cycle.

5. **Treat the API contract as a product asset**
   The contract, documentation, onboarding, and change policy are part of governance, not afterthoughts.

6. **Use governance to enable delivery**
   Governance should make good decisions faster, not become an opaque approval bottleneck.

## Lifecycle Governance Playbook

### 1. API Product Strategy

**Goal:** Confirm there is a real problem worth solving and that an API is the right product move.

**Governance focus:**
- Validate the business process or journey being improved
- Confirm target consumers and their jobs-to-be-done
- Check for existing APIs or products to reuse, buy, or extend before creating a new one
- Clarify value, viability, ownership, and success outcomes
- Identify early concept-level audit expectations

**Key questions:**
- What user or business problem are we solving?
- Who are the intended consumers and what capability do they need?
- Why is an API the right interface, instead of UI-only, batch, event, or reuse of an existing product?
- Who owns the API product and its lifecycle decisions?
- What would success look like in measurable terms?

**Expected artifacts/evidence:**
- Problem statement
- Consumer or domain analysis
- API value proposition
- Business viability notes
- Initial concept review or concept-phase checklist

**Exit criteria:**
- The API has a justified purpose, a named audience, an owner, and a clear value proposition
- Reuse/buy/build options were considered
- Major concept risks and assumptions are visible

### 2. API Consumer Experience

**Goal:** Ensure the API will be usable, adoptable, and understandable by its intended consumers.

**Governance focus:**
- Validate the developer or consumer journey early
- Identify onboarding expectations, support model, and documentation approach
- Test whether the planned API experience matches consumer capabilities and constraints

**Key questions:**
- How will consumers discover, understand, access, and test the API?
- What are the onboarding prerequisites?
- What errors, rate limits, auth flows, and support paths will consumers encounter?
- Have representative consumers reviewed the intended experience?

**Expected artifacts/evidence:**
- Consumer journey notes
- Onboarding approach
- Early docs or usage examples
- Consumer feedback or review notes

**Exit criteria:**
- The intended consumer experience is explicit and reviewable
- Onboarding and adoption friction are understood
- Consumer feedback is incorporated before implementation hardens

### 3. API Platform Architecture

**Goal:** Align the API with platform, scale, risk, and operational constraints.

**Governance focus:**
- Evaluate architectural fit, hosting context, trust boundaries, scale, and resilience needs
- Check platform standards, gateway patterns, runtime constraints, and integration dependencies
- Surface risks, mitigations, and non-functional expectations early

**Key questions:**
- Where will this API run and what platform policies apply?
- What scale, latency, availability, and regional constraints matter?
- What data sensitivity, trust, and dependency boundaries exist?
- Which risks require explicit mitigation before launch?
- What is the identity source for callers, and how are identity claims verified?
- What authorization model governs access (RBAC, ABAC, ReBAC, or a mix), and is the role/permission administration lifecycle owned and documented? (If not yet resolved, load `application-authorization`.)
- Are object-level, property-level, function-level, and tenant/multi-tenancy access controls designed and enforced at the right policy enforcement points?

**Expected artifacts/evidence:**
- Architecture notes or canvases
- Risk and impact assessment
- Capacity and deployment assumptions
- Dependency map

**Exit criteria:**
- Platform and non-functional constraints are explicit
- Key risks have owners and mitigation paths
- Architecture direction is suitable for the intended scale and environment

### 4. API Design

**Goal:** Produce a fit-for-purpose interface contract and interaction model.

**Governance focus:**
- Choose the right interaction pattern for the consumer and problem space
- Enforce consistency, naming, resource modeling, and change discipline
- Review the contract early, before code calcifies bad decisions
- Run design-phase audit checks and gather feedback

**Key questions:**
- Is the chosen style appropriate: REST, events, GraphQL, or another pattern?
- Are resources, operations, schemas, and errors consistent and understandable?
- What versioning and compatibility expectations apply?
- What review gates exist for the API contract?

**Expected artifacts/evidence:**
- Draft OpenAPI, AsyncAPI, GraphQL schema, or equivalent contract
- Design review notes
- Change policy/versioning notes
- Feedback from consumers and relevant reviewers

**Exit criteria:**
- A reviewable contract exists
- Design decisions are consistent, explainable, and aligned with consumer needs
- Early lifecycle audit checks have been completed

### 5. API Delivery

**Goal:** Build and ship the API using repeatable engineering controls.

**Governance focus:**
- Ensure implementation follows approved contract and platform expectations
- Use CI/CD, automated testing, and release controls
- Track exceptions between approved design and delivered behavior

**Key questions:**
- How is contract compliance verified during implementation?
- What automated tests cover functionality, compatibility, and operational readiness?
- How are release approvals, traceability, and rollback handled?
- Are deviations from the reviewed design documented and re-approved where needed?

**Expected artifacts/evidence:**
- CI/CD pipeline definitions
- Test suites and contract checks
- Release notes or deployment records
- Exception log for governance deviations

**Exit criteria:**
- Delivery controls are automated where possible
- The implementation is traceable to the approved contract and architecture
- Release readiness is evidenced, not assumed

### 6. API Audit

**Goal:** Confirm the API is ready for publication or broader exposure.

**Governance focus:**
- Run the full audit checklist across concept, design, delivery, and operational readiness
- Identify unresolved gaps and block publication if critical concerns remain
- Turn findings into concrete remediation actions, not vague observations

**Key questions:**
- Have all lifecycle checkpoints been satisfied?
- What remains incomplete, risky, or undocumented?
- Are exceptions explicit, approved, and time-bounded?
- Is the API ready for its intended audience and exposure model?
- **Authorization audit hooks** (load `application-authorization` if any answer is unclear):
  - Is the identity source verified and documented?
  - Is the role/permission administration lifecycle owned, with provisioning and revocation paths defined?
  - Are object-level, property-level, function-level, and tenant/cross-tenant controls covered at the intended policy enforcement points?
  - Is there negative evidence — tests or reviews confirming unauthorized, cross-tenant, or escalation paths are rejected?

**Expected artifacts/evidence:**
- Completed audit checklist
- Findings and remediation list
- Approvals or exception records

**Exit criteria:**
- Audit findings are resolved or formally accepted
- Publication readiness is evidenced
- Open risks and compensating controls are visible

### 7. API Publishing

**Goal:** Expose the API to the right audience with appropriate access, documentation, and support.

**Governance focus:**
- Publish with clear discoverability, access controls, documentation, and operational expectations
- Ensure audience segmentation matches the intended exposure model: internal, partner, public, regulated, etc.
- Make lifecycle policies visible: support, deprecation, versioning, contacts, SLAs if applicable

**Key questions:**
- Who should be able to discover and consume this API?
- What docs, examples, plans, and contacts are available at launch?
- What access approval, subscription, or key issuance process applies?
- How will consumers learn about changes and deprecations?

**Expected artifacts/evidence:**
- Published docs/portal entry
- Access and onboarding process
- Support and change communication model
- Terms/policies as applicable

**Exit criteria:**
- Consumers can discover, understand, and access the API appropriately
- Documentation and support are launch-ready
- Change and deprecation expectations are visible

### 8. Monitoring and Improvements

**Goal:** Govern the API after launch using real usage and operational feedback.

**Governance focus:**
- Measure performance, reliability, adoption, and support burden
- Review whether the API is delivering its intended value
- Feed findings back into design, platform, and product decisions
- Govern change continuously, including deprecations and improvements

**Key questions:**
- Which metrics prove the API is healthy and valuable?
- What consumer feedback loops exist?
- Which recurring incidents, support requests, or usability issues signal governance gaps?
- How are lifecycle decisions revisited over time?

**Expected artifacts/evidence:**
- Observability dashboards or metrics definitions
- Incident and support trends
- Consumer feedback summaries
- Improvement backlog and change decisions

**Exit criteria:**
- The API is monitored with meaningful indicators
- Feedback drives roadmap and governance updates
- Post-launch governance is active, not passive

## Minimum Governance Artifacts

For most APIs, governance should produce or reference at least:
- Problem statement and intended consumer definition
- Ownership and decision authority
- Architecture assumptions and risk assessment
- Reviewable API contract
- Delivery controls and test evidence
- Audit record and exceptions log
- Publication/onboarding materials
- Monitoring plan and improvement loop

## Governance Review Prompts

Use these prompts when reviewing an API initiative:

### Strategy
- What problem exists independent of the interface?
- Why should this be a new API rather than reuse of something existing?
- Who owns outcomes, not just implementation?

### Consumer Experience
- Can a real consumer understand how to get started without tribal knowledge?
- What will frustrate first-time adopters?

### Architecture
- Are platform, resilience, trust-boundary, and scale assumptions explicit?
- Which non-functional requirements are still hand-wavy?

### Design
- Does the contract reflect a coherent domain model?
- Would future changes be manageable without avoidable breakage?

### Delivery
- How do we prove implementation still matches approved design?
- Where can delivery bypass governance unintentionally?

### Audit and Publishing
- What must be true before exposure expands?
- Are documentation, access, and support paths good enough for the intended audience?

### Monitoring and Improvement
- Which signals would tell us this API is failing users even if uptime looks good?
- How are change, deprecation, and recurring issues governed over time?

## Recommended Workflow

When using this skill for a real API initiative:

1. Use the APIOps Cycles lifecycle in this skill as the main review arc.
2. Use `templates/api-governance-review.md` to capture findings, decisions, owners, and follow-ups.
3. Use `references/lifecycle-stage-control-mapping.md` to define which controls are blocking, conditional, or advisory.
4. Use `references/owasp-api-top-10.md` as a security overlay mapped to the relevant lifecycle stages.
5. Use `references/style-guides.md` to apply naming, contract, error, and consistency rules as lifecycle-stage governance rather than as a detached checklist.
6. Add organization-specific compliance policies and platform rules as overlays tied to the stages where they matter.

## Future Extensions

Add these as organization-specific overlays when available:
- API style guide rules and linting standards
- OWASP API Top 10 security checkpoints
- Data classification and privacy requirements
- Regulatory and compliance controls
- Versioning and deprecation policy templates
- Platform-specific gateway, observability, and SLO standards

Keep the APIOps Cycles lifecycle as the primary organizing arc, and layer specialized standards onto the relevant lifecycle stages instead of bolting them on as disconnected checklists.

## Common Pitfalls

1. **Treating governance as a pre-release approval meeting.**
   Governance must start at strategy and continue through operations.

2. **Jumping straight to endpoint design.**
   Teams often skip consumer, value, and architecture questions, then discover foundational problems too late.

3. **Confusing documents with decisions.**
   A filled template is not evidence unless ownership, risks, and tradeoffs are real.

4. **Ignoring consumer onboarding.**
   Technically correct APIs still fail if discovery, docs, auth, and support are weak.

5. **Allowing delivery to drift from reviewed design.**
   Governance must include contract checks, exceptions, and traceability.

6. **Stopping governance at launch.**
   Monitoring, support burden, and change management are part of governance.

7. **Adding security or style rules as detached afterthoughts.**
   Integrate them into lifecycle checkpoints where they influence decisions.

## Verification Checklist

- [ ] Governance starts at product strategy, not just design review
- [ ] Intended consumers, value, and ownership are explicit
- [ ] Platform, risk, and non-functional constraints are documented
- [ ] A reviewable API contract exists and has been socialized
- [ ] Delivery includes contract, testing, and release controls
- [ ] Audit evidence exists before publication
- [ ] Publishing covers docs, access, support, and change communication
- [ ] Monitoring and improvement loops are defined after launch
- [ ] Exceptions are explicit, visible, and time-bounded
- [ ] Additional overlays (style guides, OWASP, compliance) map to lifecycle stages rather than floating separately
