# Prisma Reference

## When to Reach for Prisma

Use Prisma when you want type-safe database access, strong TypeScript ergonomics, schema-driven modeling, and straightforward query composition for PostgreSQL, MySQL, SQLite, and related databases.

## Core Principles

- Keep Prisma calls inside services or repository-like boundaries
- Return narrow `select` shapes unless full objects are truly needed
- Use transactions for multi-step consistency
- Be deliberate about eager loading to avoid N+1 patterns

## Query Patterns

### Narrow selects

```ts
const user = await prisma.user.findUnique({
  where: { id },
  select: { id: true, email: true, name: true },
});
```

### Includes for related data

```ts
const user = await prisma.user.findUnique({
  where: { id },
  include: { posts: true, profile: true },
});
```

### Pagination

Prefer cursor pagination for stable large datasets.

```ts
const users = await prisma.user.findMany({
  take: 20,
  skip: cursor ? 1 : 0,
  cursor: cursor ? { id: cursor } : undefined,
  orderBy: { createdAt: 'desc' },
});
```

### Transactions

```ts
await prisma.$transaction(async (tx) => {
  await tx.account.update({
    where: { id: senderId },
    data: { balance: { decrement: amount } },
  });

  await tx.account.update({
    where: { id: receiverId },
    data: { balance: { increment: amount } },
  });
});
```

## Modeling Guidance

- Keep schema names aligned with domain language
- Add unique constraints intentionally
- Model soft-delete behavior explicitly if needed
- Avoid overusing JSON fields when relational modeling is clearer

## API Safety

Never return raw records that contain secrets or sensitive fields.

```ts
const user = await prisma.user.create({
  data,
  select: { id: true, email: true, name: true },
});
```

## Performance Notes

- Watch for repeated relation fetches in loops
- Prefer bulk operations when appropriate
- Inspect generated SQL when debugging slow endpoints
- Use indexes that match real filter/order usage

## Operational Notes

- Keep migrations reviewed and version-controlled
- Separate schema changes from risky app logic when possible
- Ensure deploy flow runs migrations safely

## Common Pitfalls

1. Returning full records including password hashes.
2. Doing relation lookups inside loops.
3. Using offset pagination where cursor pagination is safer.
4. Skipping transactions for multi-step balance or inventory updates.
5. Hiding too much domain logic inside giant Prisma query objects.

## Checklist

- [ ] Queries use `select` or `include` intentionally
- [ ] Sensitive fields are excluded from responses
- [ ] Transactions wrap multi-step consistency flows
- [ ] Pagination strategy matches dataset size and sort stability
- [ ] Migrations are reviewed before deployment
