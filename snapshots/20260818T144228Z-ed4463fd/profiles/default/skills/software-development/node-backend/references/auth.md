# Node Backend Auth Reference

## Auth Design Principles

Treat authentication and authorization as separate concerns.

- authentication answers who the caller is
- authorization answers what the caller may do

Keep auth flows explicit, centralized, and easy to audit.

> For RBAC model design, permission tables, tenant isolation patterns, and policy enforcement architecture, see the **`application-authorization`** skill.

## Core Patterns

### Password handling

- hash passwords with `bcrypt`, `argon2`, or another modern password hash
- never log raw passwords or password hashes unnecessarily
- compare with the library helper rather than rolling your own logic

### Token handling

For JWT-based systems:
- keep signing keys out of source control
- set explicit expiration times
- validate issuer/audience where relevant
- keep payloads minimal; avoid stuffing sensitive user state into tokens
- use **short access token lifetimes** (≤ 15 min) to bound stale-authz windows
- for sensitive or privileged actions, revalidate current role/state server-side (introspection, version field, or explicit DB check) rather than trusting embedded claims
- if you embed role/permission claims, include an `authz_version` or `roles_hash` so you can detect staleness after a privilege change

### Session or token boundary

Choose one primary approach per surface area:
- cookie/session auth for browser-first apps
- bearer tokens for APIs and service-to-service use

If you use cookies, set `httpOnly`, `secure`, and appropriate `sameSite` values.

## Authorization Patterns

Prefer policy/role checks in a dedicated layer rather than scattering `if (user.role...)` across controllers.

### Server-owned role assignment

**Never accept roles from a public-registration request payload.** Roles and permissions are server-managed; authenticated callers receive authorization context from the identity store, not from request-controlled role fields.

```typescript
// BAD — role from request body
const user = await createUser({ ...req.body, role: req.body.role });

// GOOD — reject a client-supplied role, then assign the fixed least-privilege default
if ('role' in req.body) {
  return res.status(400).json({ code: 'ROLE_NOT_ASSIGNABLE' });
}
const user = await createUser({ ...req.body, role: 'member' });
```

On public self-registration, always assign the least-privileged role (`member`, `viewer`, etc.) server-side. Privileged roles are granted only through explicit admin/back-office actions.

### Role-to-permission mapping (policy layer)

Define permissions in one place; reference them everywhere else.

```typescript
// src/authz/permissions.ts
export const ROLES = {
  admin:   ['user:read', 'user:write', 'user:delete', 'report:read'],
  editor:  ['user:read', 'user:write', 'report:read'],
  viewer:  ['user:read', 'report:read'],
  member:  ['user:read:self'],
} as const satisfies Record<string, readonly string[]>;

export type Permission = (typeof ROLES)[keyof typeof ROLES][number];

export function hasPermission(role: string, permission: Permission): boolean {
  return (ROLES[role as keyof typeof ROLES] ?? []).includes(permission);
}
```

### Express middleware — coarse route permission check

```typescript
// src/middlewares/requirePermission.ts
import { hasPermission, Permission } from '../authz/permissions';

export const requirePermission =
  (permission: Permission): RequestHandler =>
  (req, res, next) => {
    const { user } = req; // typed user attached by auth middleware
    if (user == null) {
      return res.status(401).json({ code: 'UNAUTHENTICATED' });
    }
    if (!hasPermission(user.role, permission)) {
      return res.status(403).json({ code: 'FORBIDDEN', required: permission });
    }
    next();
  };

// usage
router.delete(
  '/users/:id',
  authenticate,
  requirePermission('user:delete'),
  asyncHandler(deleteUserHandler),
);
```

### Service-level object/tenant ownership check

Route-level middleware only covers coarse access. Fine-grained ownership is enforced in the service.

```typescript
// src/services/user.service.ts
async updateUser(actorId: string, actorRole: string, targetId: string, data: UpdateUserDto) {
  // Allow: admins/editors, or the user updating their own record
  const isSelf  = actorId === targetId;
  const canEdit = hasPermission(actorRole, 'user:write') || isSelf;
  if (!canEdit) {
    throw new ForbiddenError('Cannot modify another user');
  }

  // Multi-tenant guard — actor and target must share the same tenantId
  const target = await this.db.user.findUniqueOrThrow({ where: { id: targetId } });
  if (target.tenantId !== actorTenantId(actorId)) {
    throw new ForbiddenError('Cross-tenant access denied');
  }

  return this.db.user.update({ where: { id: targetId }, data });
}
```

Examples:
- Express middleware for route-level authorization
- NestJS guards for auth + permission checks
- service-level policy checks for domain-sensitive operations

## Express Guidance

- parse and verify auth once in middleware
- attach a typed user/context object to the request
- fail closed when auth context is missing or invalid

## NestJS Guidance

Use guards for authentication and role/policy checks. Keep decorators and guards composable.

## HTTP Status Decision Guide

| Situation | Status |
|---|---|
| Missing, malformed, or expired token | **401 Unauthorized** |
| Valid identity but lacks permission | **403 Forbidden** |
| Resource exists but caller must not know | **404 Not Found** (hide existence) |
| Caller owns the token but it has been revoked | **401 Unauthorized** |

Rules of thumb:
- Return 401 when the caller is **not** (or can no longer be) authenticated.
- Return 403 when the caller **is** authenticated but the action is not permitted.
- Use 404 only when returning 403 would leak the existence of a resource that the caller should not know about (e.g., cross-tenant records).
- Never mix these up — incorrect status codes erode client error handling and audit clarity.

## Authz Audit Events

Emit a structured event for every authorization decision that matters operationally.

```typescript
// Required keys for authz audit events
interface AuthzAuditEvent {
  event:       'authz.allowed' | 'authz.denied';
  actorId:     string;         // opaque user/service ID — never PII like email
  actorRole:   string;
  permission:  string;         // e.g. 'user:delete'
  resourceType: string;        // e.g. 'User'
  resourceId:  string;         // opaque ID
  tenantId:    string | null;
  requestId:   string;         // correlation ID from request context
  timestamp:   string;         // ISO 8601
}

// Redact from audit logs: passwords, raw tokens, full auth headers,
// PII fields (email, name, phone) — log opaque IDs only.
logger.info({ ...auditEvent, password: undefined, token: undefined });
```

Indexing tip: ensure `actorId`, `permission`, `resourceId`, and `event` are indexed/queryable in your log sink so you can answer "who deleted this record?" in production.

## Token Refresh and Revocation

If the system uses refresh tokens:
- store them carefully
- rotate them on use when possible
- support revocation/logout semantics
- detect replay for high-sensitivity systems

## Testing Auth

Cover at least:
- missing credentials
- invalid credentials
- expired token/session
- authenticated but unauthorized caller
- authorized success path

### Extended negative test matrix (RBAC / multi-tenant)

| Scenario | Expected |
|---|---|
| Role boundary — `editor` attempts `user:delete` | 403 |
| Role boundary — `viewer` attempts `user:write` | 403 |
| Public self-registration sends `role: "admin"` in body | 400; server rejects client-managed roles |
| User escalates own role via PATCH `/users/:id` | 403 |
| Cross-tenant read — actor queries resource owned by another tenant | 403 or 404 |
| Non-owner update — actor edits another user's record without `user:write` | 403 |
| Token with revoked/changed role (old token, new role) — sensitive action | 403 (revalidation detects stale claim) |
| Token with `authz_version` mismatch after privilege revocation | 401 or 403 depending on revalidation strategy |
| Valid token, correct role, correct ownership — happy path | 200 / 204 |

```typescript
// Example: cross-tenant guard test
it('returns 403 when actor requests resource from a different tenant', async () => {
  const actorToken = signToken({ sub: 'user-a', tenantId: 'tenant-1', role: 'editor' });

  await request(app)
    .get('/api/reports/report-owned-by-tenant-2')
    .set('Authorization', `Bearer ${actorToken}`)
    .expect(403);
});

// Example: public self-escalation attempt
it('rejects a role field in the public registration body', async () => {
  await request(app)
    .post('/api/auth/register')
    .send({ email: 'new@example.com', password: 'S3cure!', role: 'admin' })
    .expect(400)
    .expect({ code: 'ROLE_NOT_ASSIGNABLE' });
});
```

## Common Pitfalls

1. Mixing auth logic directly into controllers.
2. Returning overly specific login failure messages that aid enumeration.
3. Using long-lived tokens without rotation or revocation strategy.
4. Forgetting authorization checks after authentication succeeds.
5. Logging full tokens or auth headers.
6. Accepting privileged roles from the request body on registration or self-update.
7. Trusting long-lived JWT role claims for sensitive actions without server-side revalidation (stale-authz window).
8. Checking authentication but skipping cross-tenant / object ownership at the service layer.
9. Returning 403 when existence should be hidden — use 404 for cross-tenant resource access.
10. Missing audit events for authorization denials, making production incidents hard to diagnose.

## Checklist

- [ ] Passwords are hashed with a modern algorithm
- [ ] Tokens/sessions use explicit expiration and secure storage
- [ ] Authentication and authorization are separated cleanly
- [ ] Protected routes fail closed by default
- [ ] Roles are assigned server-side; privileged roles never accepted from request input
- [ ] Role-to-permission mapping lives in one dedicated policy layer
- [ ] Route middleware enforces coarse permission; service layer enforces object/tenant ownership
- [ ] Access token lifetime is short (≤ 15 min); sensitive actions revalidate role server-side
- [ ] 401/403/404 used correctly (see HTTP Status Decision Guide)
- [ ] Authz audit events emitted with required keys; PII redacted
- [ ] Tests cover unauthenticated, unauthorized, and authorized cases
- [ ] Extended negative matrix covers role boundary, self-escalation, cross-tenant, revoked-role scenarios
