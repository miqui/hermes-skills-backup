# API Governance lifecycle stage-to-control mapping

This reference turns the APIOps Cycles lifecycle into a control matrix. Use it to define what is governed, what evidence is expected, and who typically approves or contributes.

## How to use this matrix

For each lifecycle stage:
- identify the control objectives
- define concrete evidence
- assign accountable owners/reviewers
- decide whether a failed control blocks progress, requires an exception, or is advisory

## Stage-to-control matrix

| Lifecycle stage | Governance objective | Example controls | Expected evidence | Typical stakeholders |
|---|---|---|---|---|
| API Product Strategy | Ensure the API is worth creating and has accountable ownership | Problem statement required; consumer identified; reuse/buy/build review required; success metrics defined | Problem statement, value proposition, ownership record, alternatives analysis | Product owner, domain lead, architect |
| API Consumer Experience | Ensure the API is adoptable and understandable | Onboarding path defined; auth/access journey reviewed; example quality reviewed; consumer validation required | Onboarding draft, docs outline, sample flows, consumer feedback | Product owner, developer experience, consumer representatives |
| API Platform Architecture | Ensure platform fit, risk visibility, and non-functional alignment | Architecture review; dependency/trust-boundary review; capacity/location assumptions; risk register entry | Architecture decision notes, dependency map, risk register, NFR summary | Architect, platform team, security, SRE |
| API Design | Ensure the contract is coherent, consistent, and governable | Contract review; naming/resource conventions; versioning/change policy; style linting if available | OpenAPI/AsyncAPI/schema, design review notes, lint output, versioning notes | API designer, architect, platform/API guild |
| API Delivery | Ensure implementation remains aligned with approved design | CI/CD policy; contract tests; automated quality gates; exception handling for drift | Pipeline config, test results, release records, exception log | Engineering lead, delivery team, QA/platform |
| API Audit | Ensure unresolved governance gaps are visible before wider exposure | Formal readiness review; findings log; exception approval workflow; go/no-go criteria | Completed checklist, findings list, approvals, remediation plan | Governance board, architect, security, product owner |
| API Publishing | Ensure the API is exposed correctly and supportably | Audience/access review; docs completeness check; portal registration; support contact defined | Portal entry, published docs, access workflow, support/change policy | API platform team, product owner, support/devrel |
| Monitoring and Improvements | Ensure post-launch behavior informs governance and change decisions | Metrics review; incident trend review; feedback loop; deprecation/change governance | Dashboards, incident summaries, consumer feedback, improvement backlog | Product owner, SRE, support, platform team |

## Control design guidance

### Decide control type
Classify each control as:
- **Preventive** — stops bad decisions early
- **Detective** — reveals drift or risk after the fact
- **Corrective** — drives remediation and improvement

A mature governance model uses all three.

### Decide enforcement mode
For each control, decide whether it is:
- **Blocking** — must pass before moving forward
- **Conditional** — can proceed only with approved exception
- **Advisory** — important guidance but not a hard gate

### Decide evidence quality
Prefer evidence that is:
- reviewable by others
- durable and linked to ownership
- generated from real artifacts where possible
- specific enough to support audit and follow-up

Weak evidence examples:
- verbal confirmation
- undocumented assumptions
- generic “covered in Jira” notes with no linked artifact

Strong evidence examples:
- approved design record
- contract artifact and lint output
- linked test results
- explicit exception with owner and expiry
- dashboard or incident report proving operational follow-through

## Sample overlay mapping

Examples of how specialized concerns map onto the lifecycle instead of floating outside it:

| Overlay concern | Best-fit lifecycle stages |
|---|---|
| API style guide | Design, Delivery, Audit |
| OWASP API Top 10 | Strategy, Architecture, Design, Delivery, Audit, Monitoring |
| Versioning/deprecation policy | Design, Publishing, Monitoring |
| Data classification/privacy | Strategy, Architecture, Design, Audit |
| SLOs/operational policy | Architecture, Delivery, Monitoring |

## Practical rule

If a control has no clear lifecycle stage, owner, or evidence requirement, it is not yet governable.