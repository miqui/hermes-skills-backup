# APIOps Cycles — New API reference summary

Source: https://www.apiopscycles.com/getting-started/new-api/
Title: New API | APIOps Cycles

## Purpose

This reference captures the lifecycle backbone used by the `api-governance` skill. It is not a replacement for the source. It exists so the skill can preserve the governing arc while remaining easy to extend with additional overlays later.

## Core lifecycle from the source

1. **API Product Strategy**
   - Customer Journey Canvas
   - Domain Canvas
   - API Value Proposition Canvas
   - API Business Model Canvas
   - Get familiar with the concept-phase API Audit Checklist and share for feedback

2. **API Consumer Experience**
   - Validate plans with consumers
   - Plan onboarding

3. **API Platform Architecture**
   - Business Impact Canvas
   - Capacity Canvas
   - Location Canvas

4. **API Design**
   - Interaction Canvas
   - Choose the right interface pattern: REST, Event, GraphQL, etc.
   - Draft the contract (OpenAPI or equivalent)
   - Do the first two phases of the API Audit Checklist and share with consumers for feedback

5. **API Delivery**
   - Follow internal CI/CD, test automation, and release practices

6. **API Audit**
   - Do the full API Audit using the API Audit Checklist
   - Prepare for publishing

7. **API Publishing**
   - Expose APIs securely and clearly to the right audience with the right documentation and processes

8. **Monitoring and Improvements**
   - Use metrics and feedback to track performance and drive continuous improvement

## Governance interpretation

The key governance takeaway is that the source does **not** place governance in a single isolated review stage. Instead, it implies staged governance across:
- value and ownership
- consumer validation
- architecture and risk
- design and contract quality
- delivery controls
- audit readiness
- publication controls
- post-launch improvement loops

That makes APIOps Cycles a good backbone for lifecycle governance: each stage can carry its own policies, reviews, and evidence requirements.

## Suggested future overlays

The skill should later add supporting guidance for:
- enterprise API style guides and naming conventions
- OWASP API Top 10 mapped to design, delivery, publishing, and monitoring stages
- versioning and deprecation policy
- API product metrics and platform SLOs
- privacy, data classification, and regulatory controls
- contract linting and governance automation

## Skill design note

When extending the skill, keep APIOps Cycles as the main organizing arc. Do not bolt on extra concerns as disconnected appendices if they can be mapped to a lifecycle stage.
