---
name: application-authorization
description: "Use when designing, implementing, reviewing, or testing production application authorization: RBAC role lifecycle, multi-layer enforcement, tenant/object/property controls, authorization-claim freshness, audit evidence, and RBAC-to-ABAC/ReBAC decisions."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [authorization, rbac, abac, rebac, security, access-control, jwt, audit]
    related_skills: [node-backend, graphql-api, grpc-api, api-governance, fastify-oauth, playwright-testing]
---

# Application Authorization

## Overview

Authorization answers **"is this authenticated identity allowed to perform this action on this resource?"** It is distinct from authentication, which establishes identity. Enforce authorization at every relevant layer rather than treating a successful login as permission to act.

## When to Use

- Designing or reviewing a role, permission, assignment, or policy model.
- Adding authorization middleware, guards, service policies, or tenant scoping.
- Investigating privilege escalation, incorrect 401/403 behavior, or cross-tenant access.
- Handling permission changes during active JWT sessions.
- Choosing between RBAC, ABAC, ReBAC, or a policy engine.
- Adding authorization integration, API, or end-to-end tests and audit evidence.

Do not use this skill as the primary guide for:
- Pure authentication flows such as login, token issuance, or session creation; use `fastify-oauth` or the runtime-specific backend skill.
- Network firewall, VPC, or security-group controls; use the relevant infrastructure skill.


---

## 1. RBAC Model Design

### Core primitives
| Primitive | Description |
|-----------|-------------|
| **Permission** | Atomic capability string: `resource:action` (e.g. `invoice:read`, `user:delete`) |
| **Role** | Named collection of permissions (e.g. `viewer`, `editor`, `admin`) |
| **Assignment** | Binding of a role to a principal (user, service account, group) within a scope (tenant, project) |

### Naming conventions
- Use `noun:verb` for permissions (`report:export`, `billing:update`).
- Role names should reflect business function, not technical level (`auditor` not `read_only`).
- Scope permissions to the bounded context that owns the resource.

### Role hierarchy cautions
Role inheritance (`admin` inherits `editor` inherits `viewer`) reduces duplication but introduces risks:
- **Privilege explosion**: a change to a parent role silently escalates all child principals.
- **Audit opacity**: effective permissions become non-obvious without tooling.
- **Mitigation**: limit hierarchy depth to ≤ 2; always resolve and log *effective* permissions at enforcement time, not just the assigned role name.

### Permission granularity tradeoffs
| Granularity | Pros | Cons |
|-------------|------|------|
| Coarse (`admin` / `viewer`) | Simple, fast | Over-broad grants |
| Medium (`resource:action`) | Balanced | Moderate overhead |
| Fine (`resource:action:field`) | Precise | Combinatorial explosion, harder to explain to users |

Start at medium granularity; promote specific fields to fine-grained only when least-privilege audits reveal real exposure.

---

## 2. Secure Role Lifecycle & Provisioning

### Public registration
- **Fixed default role only.** New registrations must receive the minimum least-privilege role (e.g. `member` or `viewer`) hard-coded in the registration handler.
- Never read a `role` field from the registration request body. Validate and reject any attempt.
- Default role must be explicit in code — avoid relying on a DB default that can drift.

```
// pseudo-code — framework-neutral
function registerUser(requestBody) {
  const user = { ...sanitize(requestBody), role: ROLES.MEMBER }; // role is server-assigned
  return userRepository.create(user);
}
```

### Elevation & demotion
- Role elevation must require a separate, authenticated privileged action by an authorized actor (not the target user).
- Log: `who elevated`, `from role`, `to role`, `timestamp`, `reason` (if required by policy).
- Send an out-of-band notification to the target user when their role changes.

### Revocation
- Revocation must propagate within the session window defined by your JWT freshness policy (see §6).
- Soft-delete or deactivate: never hard-delete role assignments without archiving them; revoked assignments are audit evidence.
- When revoking access for a terminated user: disable account AND revoke refresh tokens AND (if JWT-based) add to a short-lived revocation list or shorten token TTL.

### Audit trail requirements
Every role assignment, elevation, demotion, and revocation must emit a structured audit event (see §7).

---

## 3. Enforcement Layers

Authorization must be enforced at **every layer independently**. Relying on a single layer is a common source of privilege escalation.

### Layer 1 — Boundary / HTTP middleware
Enforces coarse-grained access before the request enters business logic.

Checks:
- Is the token present and valid? → 401 if not
- Does the caller's role include any permission in the required set? → 403 if not
- Is the tenant/scope in the token consistent with the route? → 403 if not

```
// pseudo-code
async function requirePermission(requiredPermission) {
  return async (ctx, next) => {
    const principal = ctx.state.principal; // set by auth middleware upstream
    if (!principal) throw new HttpError(401, "Unauthenticated");
    if (!principal.hasPermission(requiredPermission)) {
      auditDeny(principal, requiredPermission, ctx.url);
      throw new HttpError(403, "Forbidden");
    }
    await next();
  };
}
```

### Layer 2 — Domain / service
Enforces **object-level** authorization: does the principal own or otherwise have rights to this specific resource instance?

This layer cannot be replaced by the boundary layer — it requires loading the resource and inspecting ownership or assignment.

```
// pseudo-code
function assertCanEditDocument(principal, document) {
  const allowed =
    principal.hasPermission("document:edit") &&
    (document.ownerId === principal.id ||
      document.collaborators.includes(principal.id) ||
      principal.hasRole("admin"));

  if (!allowed) {
    auditDeny(principal, "document:edit", document.id);
    throw new ForbiddenError();
  }
}
```

### Layer 3 — Query / data scoping
Prevents mass data exposure by injecting authorization filters at the data-access level.

```
// pseudo-code — repository layer
function listDocuments(principal) {
  if (principal.hasRole("admin")) {
    return db.documents.findAll();
  }
  return db.documents.findAll({
    where: { ownerId: principal.id }   // always filter by principal scope
  });
}
```

---

## 4. Fine-Grained Authorization Patterns

### Function (action) authorization
Gate individual operations on permissions: `invoice:approve`, `report:export`. Enforce in the service method, not just the route.

### Object (resource instance) authorization
Load the object, check ownership/assignment. Never authorize based on ID alone. See Layer 2 above.

### Property (field-level) authorization
Certain fields on a response must be hidden or redacted based on role:

```
// pseudo-code
function serializeUser(user, principal) {
  const dto = { id: user.id, name: user.name, email: user.email };
  if (principal.hasPermission("user:read:salary")) {
    dto.salary = user.salary;
  }
  // salary is absent from the DTO if not permitted — not null, not "REDACTED"
  return dto;
}
```

Prefer *omission* over substitution; substitution leaks the field's existence and type.

### Tenant (multi-tenant) authorization
- Store `tenantId` on every resource row.
- Validate `principal.tenantId === resource.tenantId` before any object-level operation.
- Inject tenant filter in every query — never rely on the caller to supply the correct tenantId filter.
- Cross-tenant access (e.g. support/admin roles) requires an explicit, separately audited mechanism.

---

## 5. REST Status Code Semantics

| Scenario | Code | Notes |
|----------|------|-------|
| No credentials present | **401** | Include `WWW-Authenticate` header |
| Credentials invalid or expired | **401** | Do not distinguish expired vs invalid in the body |
| Authenticated but insufficient permission | **403** | Body may state "Forbidden" without leaking resource details |
| Resource doesn't exist OR caller lacks permission to know it exists | **404** | Use existence-hiding when the resource ID itself is sensitive (e.g. private user profiles, draft documents) |
| Action not permitted on resource in current state | **403** | Prefer 403 over a custom code; include a machine-readable `code` in the body |

**Existence-hiding guideline**: Return 404 instead of 403 only when confirming the resource exists would itself leak sensitive information. Be consistent — mixing 403/404 for the same resource type confuses clients and can break caches. Document the chosen behavior in your API contract.

---

## 6. JWT Authorization-Claim Freshness & Revocation

### The freshness problem
JWTs are self-contained; permissions baked into the token are stale after role changes. The token remains valid until expiry.

### Strategies (choose based on sensitivity)

| Strategy | Staleness window | Complexity |
|----------|-----------------|------------|
| Short-lived access tokens (≤5 min) | ≤ token TTL | Low — just shorten TTL |
| Permissions fetched from DB on each request (token as identity only) | None | Medium — adds DB latency |
| Token introspection endpoint | Configurable (cache TTL) | Medium |
| Revocation list (blocklist by `jti`) | Until list checked | Medium — list must be fast (Redis) |
| Phantom token / reference token | None | Higher — gateway exchanges opaque token for JWT internally |

### Practical guidance
- Separate **access token TTL** (short: 5–15 min) from **refresh token TTL** (long: days/weeks).
- Include only stable claims in the JWT (`sub`, `tenantId`, `sessionId`). Fetch volatile permissions from a fast store per request or use short TTL.
- On role revocation: invalidate all outstanding refresh tokens for the affected user; the short access token TTL bounds the blast radius.
- Never include sensitive PII or full permission lists in JWT payloads that traverse untrusted clients unless the payload is encrypted (JWE).

---

## 7. Structured Authorization Decision Auditing

Every authorization decision (allow **and** deny) should be auditable. Prefer structured logs over plain text.

### Audit event schema

```json
{
  "eventType": "authorization.decision",
  "outcome": "deny",
  "timestamp": "2026-07-11T14:23:01.482Z",
  "requestId": "req_8f3a...",
  "principal": {
    "id": "usr_abc123",
    "tenantId": "tenant_xyz",
    "role": "editor"
  },
  "action": "invoice:approve",
  "resource": {
    "type": "invoice",
    "id": "inv_9912"
  },
  "reason": "role_insufficient",
  "sourceIp": "10.0.1.4",
  "userAgent": "MyApp/2.1"
}
```

### Redaction rules
- **Do** log resource type and a stable, non-sensitive resource ID.
- **Do not** log resource field values (invoice amount, patient data, etc.) in the authorization event — that belongs in a separate data-access audit trail with stricter controls.
- **Do not** log raw JWT tokens or secrets.
- Mask PII fields (email, name) if your compliance context requires it; use a stable pseudonymous ID instead.

### Storage and retention
- Authorization deny events are high-signal security indicators; route them to a separate, append-only, tamper-evident store or SIEM.
- Retain according to your compliance requirements (commonly 1–7 years). Plan for storage cost at scale.

---

## 8. Authorization Testing Matrix

Cover these test dimensions in integration and E2E tests:

| Dimension | What to test |
|-----------|--------------|
| **Happy path** | Correct role can perform permitted action on owned resource |
| **Role boundary** | Role one step below required is correctly denied |
| **Object ownership** | User cannot access another user's resource even with same role |
| **Tenant isolation** | User in Tenant A cannot access Tenant B resources under any role |
| **Privilege escalation** | Registration/update endpoint cannot self-assign elevated role |
| **Existence hiding** | 404 (not 403) returned when resource is private and existence is sensitive |
| **Field redaction** | Restricted fields absent from response for unpermitted roles |
| **Revocation** | After role downgrade, previously permitted action is denied |
| **Token freshness** | Expired token returns 401; valid token with stale role hits freshness policy |
| **Cross-role** | Admin can act on all objects; `viewer` cannot mutate |

### Test structure (framework-neutral)

```
describe("Authorization: invoice:approve", () => {
  test("finance_manager can approve an own-tenant invoice", ...);
  test("editor is denied invoice:approve (403)", ...);
  test("finance_manager in tenant_A cannot approve tenant_B invoice", ...);
  test("anonymous request returns 401", ...);
});
```

Use the `playwright-testing` skill for browser/E2E authorization flows.
Use `graphql-api` or `grpc-api` skill patterns for field-level and operation-level authorization testing in those protocols.

---

## 9. RBAC vs ABAC vs ReBAC — Decision Guide

| Model | Best fit | Complexity | Example use case |
|-------|----------|------------|-----------------|
| **RBAC** | Stable roles, coarse-grained access, small permission set | Low | SaaS app with `admin/editor/viewer` per workspace |
| **ABAC** | Access depends on resource attributes (status, classification, geography) | Medium–High | Healthcare: role=doctor AND resource.department=oncology |
| **ReBAC** | Access derived from relationships between entities | High | Google Docs–style sharing: user→folder→document |
| **Hybrid** | Most real-world apps at scale | Varies | RBAC for coarse gates + ABAC for fine-grained conditions |

**Choose RBAC when**: roles map cleanly to business functions, the number of roles is small (< ~20), and conditions on resource attributes are minimal.

**Move toward ABAC when**: you find yourself creating many fine-grained roles to encode attribute conditions (`editor_in_us`, `editor_in_eu`).

**Consider ReBAC when**: access propagates along object graphs (shares, parent-child ownership, group membership) and graph traversal is the natural model.

---

## 10. Policy Engine Decision Criteria

A dedicated policy engine separates authorization logic from application code, enabling centralized governance, auditing, and policy-as-code.

**Evaluate a policy engine when**:
- Authorization logic is duplicated across multiple services (microservices, multiple backends).
- Non-engineers (compliance, legal) must review or modify access rules.
- You need an audit trail of *why* a decision was made (policy evaluation trace).
- Rule complexity exceeds what is manageable in application code (many conditions, attributes).

**Lightweight alternatives first**: for a single service with stable roles, inline enforcement (Layers 1–3 above) is simpler, faster, and has fewer failure modes than an external engine.

**Policy engine landscape (examples only — evaluate against your requirements)**:
- **OPA (Open Policy Agent)**: general-purpose Rego-based policy evaluation; widely used for microservices and Kubernetes.
- **Cedar**: attribute-based, designed for application authorization with a formally verified evaluation model.
- **Casbin**: embeddable, supports RBAC/ABAC/ACL models; integrates directly into application code.
- **SpiceDB / Zanzibar-style**: relationship-based (ReBAC) with a graph store; suited for Google Docs–style sharing models.

**Decision criteria**:
1. Does the model fit (RBAC→Casbin, ABAC→OPA/Cedar, ReBAC→SpiceDB)?
2. Can your team operate the engine's infrastructure and debug policy evaluation errors?
3. Does the engine support your audit/tracing requirements?
4. What is the added latency for per-request policy evaluation, and is it acceptable?

---

## Review Reference

- `references/route-rbac-review-pattern.md` — repeatable review rubric for tutorials and implementations that present route middleware as an RBAC solution; covers provisioning escalation, object/tenant enforcement, stale claims, denial semantics, auditability, and negative evidence.

## Common Pitfalls

1. **Authentication-only middleware**: protecting the route but not the object — passes role check but doesn't verify resource ownership.
2. **Role in request body**: accepting `role: "admin"` from registration or update payloads.
3. **Existence leakage via timing**: returning 403 faster for "exists but forbidden" than for "not found" — use consistent response timing.
4. **Mutable JWT permissions**: baking `permissions: [...]` into long-lived JWTs; role changes don't take effect until expiry.
5. **Missing tenant filter in queries**: fetching all records and filtering in application code — broken under pagination and race conditions.
6. **Audit logging only denies**: allows are equally important for detecting over-broad grants.
7. **Authorization in the view layer only**: client-side UI hiding of buttons is UX, not security — all enforcement must be server-side.
8. **God role proliferation**: a single `superadmin` role that bypasses all checks — model it explicitly with its own audit trail, don't make it invisible to the enforcement code.
9. **Cascading role deletion**: deleting a role without first reassigning or explicitly revoking its principals leaves orphaned assignments.
10. **Skipping cross-tenant tests**: often added late; tenant isolation bugs are among the most severe in SaaS applications.

---

## Verification Checklist

- [ ] Registration endpoint rejects any client-supplied role field; the fixed default role is assigned server-side
- [ ] Default role is hard-coded server-side, not DB-default-only
- [ ] Every HTTP route has explicit permission requirement documented and enforced
- [ ] Object-level ownership check is enforced in the service layer (not just middleware)
- [ ] All queries inject a tenant/scope filter; no unscoped queries to multi-tenant tables
- [ ] Field-level redaction tested for at least one sensitive field
- [ ] JWT access token TTL ≤ 15 min OR permissions are fetched from store per request
- [ ] Role revocation invalidates refresh tokens and is covered by a test
- [ ] Authorization deny events are logged with structured schema
- [ ] Audit log does not contain raw JWT tokens, passwords, or unredacted PII
- [ ] Authorization testing matrix covers all 10 dimensions in §8
- [ ] 401 vs 403 semantics are consistent and documented in the API contract
- [ ] Existence-hiding behavior is explicit and consistent per resource type
- [ ] Any policy engine choice is justified against the decision criteria in §10
