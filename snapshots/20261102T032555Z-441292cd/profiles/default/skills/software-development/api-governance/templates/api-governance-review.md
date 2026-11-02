# API Governance Review

> Use this template to review a new or evolving API against the APIOps Cycles lifecycle. Replace bracketed placeholders and delete sections that do not apply.

## Review Metadata

- API / initiative:
- Review date:
- Review type: [new API | redesign | pre-publish audit | periodic review]
- Review owner:
- Product owner:
- Technical owner:
- Intended audience: [internal | partner | public | other]
- Exposure level:
- Decision status: [approved | approved with conditions | blocked | needs follow-up]

---

## 1. API Product Strategy

### Summary
- Problem being solved:
- Intended consumers:
- Why an API is the right product move:
- Reuse/buy/build alternatives considered:
- Success measures:

### Governance checks
- [ ] Problem statement is explicit
- [ ] Intended consumers are identified
- [ ] Owner and decision authority are clear
- [ ] Existing alternatives were considered
- [ ] Value proposition is documented

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 2. API Consumer Experience

### Summary
- Consumer journey:
- Onboarding approach:
- Authentication/access model:
- Docs/examples planned:
- Consumer validation completed:

### Governance checks
- [ ] Consumer onboarding path is defined
- [ ] Consumer friction points are understood
- [ ] Docs/examples are planned or drafted
- [ ] Feedback from representative consumers was gathered

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 3. API Platform Architecture

### Summary
- Platform/runtime context:
- Key dependencies:
- Scale and resilience assumptions:
- Trust boundaries / data sensitivity:
- Key risks and mitigations:

### Governance checks
- [ ] Platform constraints are explicit
- [ ] Key dependencies are documented
- [ ] Risks and mitigations are identified
- [ ] Non-functional expectations are defined

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 4. API Design

### Summary
- Interaction style: [REST | events | GraphQL | other]
- Contract artifact:
- Versioning/change approach:
- Design review participants:

### Governance checks
- [ ] Reviewable contract exists
- [ ] Resource/schema/error patterns are coherent
- [ ] Versioning/change policy is defined
- [ ] Consumer/reviewer feedback was incorporated

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 5. API Delivery

### Summary
- Delivery approach / CI-CD:
- Test evidence:
- Contract verification approach:
- Release/rollback approach:
- Known deviations from approved design:

### Governance checks
- [ ] Delivery controls are defined
- [ ] Automated testing exists or is planned
- [ ] Contract/design conformance is verified
- [ ] Deviations are documented and reviewed

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 6. API Audit

### Summary
- Audit scope:
- Open findings:
- Exceptions requested/approved:
- Publication readiness assessment:

### Governance checks
- [ ] Lifecycle checkpoints were reviewed
- [ ] Findings are recorded with owners
- [ ] Exceptions are explicit and time-bounded
- [ ] Readiness decision is evidence-based

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 7. API Publishing

### Summary
- Publication target / portal:
- Access/subscription model:
- Documentation status:
- Support/change communication model:

### Governance checks
- [ ] Intended audience matches exposure model
- [ ] Docs and onboarding are launch-ready
- [ ] Access process is defined
- [ ] Support and change communication are visible

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## 8. Monitoring and Improvements

### Summary
- Key operational metrics:
- Consumer feedback loops:
- Incident/support review process:
- Improvement backlog/process:

### Governance checks
- [ ] Monitoring signals are defined
- [ ] Feedback loops exist
- [ ] Operational review process exists
- [ ] Improvement path is assigned

### Findings / decisions
- Strengths:
- Gaps:
- Required actions:

---

## Overlay Checks

### Security / OWASP API Top 10
- Relevant concerns:
- Stage(s) where addressed:
- Remaining security risks:

### Style Guide / Design Standards
- Applicable style guide:
- Linting/review status:
- Exceptions:

### Compliance / Privacy / Data Controls
- Applicable controls:
- Evidence:
- Open gaps:

---

## Final Decision

### Decision
- Status:
- Approved by:
- Date:

### Conditions / follow-ups
1.
2.
3.

### Exception log
- Exception:
- Rationale:
- Owner:
- Expiration/review date:
