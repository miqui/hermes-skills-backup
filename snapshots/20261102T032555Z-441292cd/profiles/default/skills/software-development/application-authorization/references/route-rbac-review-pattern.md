# Route-Level RBAC Review Pattern

## Trigger

Use this reference when reviewing a tutorial, code sample, or implementation that presents route middleware such as `requireRole('admin')` or `checkRole('editor', 'admin')` as an RBAC solution.

## What route-level RBAC does cover

- Authenticated identity reaches the request context.
- A coarse permission or role gate runs before a handler.
- Function-level authorization is visible at route registration.
- Basic deny-path testing can verify that a lower-privilege caller is blocked.

This is appropriate as an introductory pattern, but it is only one authorization layer.

## Mandatory review checks

### 1. Provisioning boundary

Public registration must not accept a role, permission, or admin flag from the request body. Assign the fixed least-privilege default server-side; role changes belong to a separate, authorized administrative workflow.

**Fail condition:** a caller can submit `role: 'admin'` (or equivalent) and obtain the role merely because it is in an allowlist.

### 2. Enforcement depth

Route middleware protects an operation category; it does not establish authority over a specific object. Confirm that sensitive domain actions also perform:

- ownership or assignment checks;
- tenant/scope checks;
- query-level scoping so lists cannot leak other tenants' data;
- field/property filtering where response fields have different sensitivity.

### 3. Authorization-claim freshness

If a token carries roles or permissions, define what happens after elevation, demotion, user disablement, or revocation. Use a bounded stale window through short access-token TTLs, server-side revalidation/versioning, or introspection as sensitivity requires.

### 4. REST denial semantics

- `401`: missing, invalid, expired, or revoked authentication state.
- `403`: authenticated caller lacks permission.
- `404`: only when resource existence itself must be hidden; apply consistently by resource type.

Do not expose role inventory or detailed policy internals in denial responses.

### 5. Negative evidence

At minimum, test:

| Case | Expected result |
| --- | --- |
| Unauthenticated request | 401 |
| Authenticated lower-role request | 403 |
| Public registration with privileged role field | rejection; no account/role escalation |
| Non-owner or cross-tenant access | 403 or documented existence-hiding 404 |
| Role downgrade/revocation with an old access token | denied according to freshness policy |
| Allowed role, correct tenant, and owned/assigned object | success |

### 6. Auditability

For privileged allow and deny decisions, record: principal ID, tenant/scope, effective role or permission, action, resource type/opaque ID, outcome, reason code, timestamp, and correlation ID. Do not record raw tokens, authorization headers, passwords, or unnecessary PII.

## Review conclusion template

> The implementation provides route-level/function-level RBAC. Before calling it production-ready, require server-owned role provisioning, object and tenant enforcement below the route layer, a role-claim freshness policy, denial semantics, structured audit events, and the negative test matrix above.
