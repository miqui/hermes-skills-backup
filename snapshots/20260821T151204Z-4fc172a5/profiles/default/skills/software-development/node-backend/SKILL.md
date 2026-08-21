---
name: node-backend
description: "Use when working with Node.js backends using Express, NestJS, Fastify, REST/GraphQL APIs, controllers, services, validation, logging, security, testing, and backend architecture."
version: 1.0.0
author: Miguel Quintero
license: MIT
metadata:
  hermes:
    tags: [nodejs, node, express, nestjs, fastify, backend, api, typescript, prisma, zod, hapi]
    related_skills: [systematic-debugging, test-driven-development, graphql-api, code-performance-engineering]
---

# Node.js Backend

## Overview

Expert-level Node.js backend patterns for Express, NestJS, Fastify, and API development. Use this skill to structure services cleanly, validate inputs, handle errors consistently, improve async behavior, secure endpoints, and write maintainable tests.

For GraphQL schema design, resolver boundaries, query cost controls, batching/DataLoader patterns, and contract evolution, pair this skill with `graphql-api`. For endpoint latency, throughput, ORM/query performance, GraphQL resolver fan-out, async bottlenecks, N+1 calls, or memory/CPU pressure, pair with `code-performance-engineering` so changes include representative baselines, profiling or tracing evidence, and Big-O reasoning where input growth matters.

## Linked References

- `references/express.md` — Express-specific architecture, middleware ordering, validation boundaries, and testing guidance
- `references/nestjs.md` — NestJS module boundaries, DTOs, guards, interceptors, validation pipes, and testing guidance
- `references/fastify.md` — Fastify plugin architecture, route schemas, hooks, decorators, and testing guidance
- `references/prisma.md` — Prisma query shape, transactions, pagination, modeling, and operational guidance
- `references/testing.md` — Layered testing strategy, factories, HTTP/integration coverage, and database test guidance
- `references/auth.md` — Authentication, authorization, token/session handling, and protected route guidance
- `references/graphql.md` — GraphQL schema, resolver boundaries, batching, query cost, and testing guidance
- `references/observability.md` — Structured logging, metrics, traces, health checks, and alerting guidance
- `references/websockets.md` — WebSocket connection lifecycle, event contracts, rooms, auth, and scaling guidance
- `references/hapi.md` — Hapi server/route mechanics, plugins/decorations, Joi validation, auth scheme/strategy wiring, and `server.inject()` testing guidance

## When to Use

- Building or refactoring Node.js backend services
- Working on Express, NestJS, or Fastify applications
- Adding or reviewing REST or GraphQL API endpoints
- Working with controllers, services, DTOs, middleware, validators, or repositories
- Improving backend architecture, observability, security, and test coverage

Don't use for:
- Frontend-only React, Vue, or UI styling work
- Pure infrastructure tasks with no Node.js application code
- Browser automation tasks unrelated to backend services

## Auto-Detection

This skill is especially relevant when:
- The project uses `express`, `@nestjs/core`, `fastify`, or `@hapi/hapi`
- The task involves authentication, authorization, route protection, or login/session flows
- The work focuses on backend test architecture, integration coverage, or endpoint verification
- The task involves GraphQL schema design, resolvers, mutations, or query performance
- The work focuses on logging, metrics, tracing, health checks, or alerting
- The task involves WebSockets, socket events, rooms, presence, or real-time delivery
- The codebase includes `*.controller.ts`, `*.service.ts`, or route modules
- The task involves APIs, auth, validation, database access, or background jobs
- The work is on a TypeScript Node backend or service layer

## Project Structure

For framework-specific project layout and operational guidance, see:
- `references/express.md`
- `references/nestjs.md`
- `references/fastify.md`

### Express (MVC-style)

```text
src/
├── config/           # Configuration
├── controllers/      # Route handlers
├── models/           # Database models
├── routes/           # Route definitions
├── middlewares/      # Custom middleware
├── services/         # Business logic
├── utils/            # Utilities
├── validators/       # Request validation
├── app.ts            # Express setup
└── server.ts         # Entry point
```

### NestJS (modular)

```text
src/
├── modules/
│   └── users/
│       ├── users.controller.ts
│       ├── users.service.ts
│       ├── users.module.ts
│       ├── dto/
│       └── entities/
├── common/
│   ├── guards/
│   ├── interceptors/
│   └── filters/
├── app.module.ts
└── main.ts
```

### Fastify (plugin-oriented)

```text
src/
├── plugins/
├── routes/
├── controllers/
├── services/
├── schemas/
├── hooks/
├── app.ts
└── server.ts
```

## Express Patterns

For more Express-specific guidance on app bootstrap, middleware ordering, validation boundaries, and testing, see `references/express.md`.

### Async error wrapper

```typescript
const asyncHandler = (fn: RequestHandler): RequestHandler => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

router.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  if (user == null) {
    throw new NotFoundError('User');
  }
  res.json({ data: user });
}));
```

### Custom error classes

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = 'INTERNAL_ERROR',
    public isOperational: boolean = true,
  ) {
    super(message);
    Error.captureStackTrace(this, this.constructor);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

class ValidationError extends AppError {
  constructor(message: string, public details?: Record<string, string[]>) {
    super(message, 400, 'VALIDATION_ERROR');
  }
}
```

### Global error handler

```typescript
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      status: 'error',
      code: err.code,
      message: err.message,
    });
  }

  logger.error('Unexpected error', { error: err, path: req.path });

  res.status(500).json({
    status: 'error',
    code: 'INTERNAL_ERROR',
    message: 'Something went wrong',
  });
});
```

## NestJS Patterns

For more NestJS-specific guidance on module boundaries, global validation pipes, guards, interceptors, and testing, see `references/nestjs.md`.

### Controller with validation

```typescript
@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {}

  @Post()
  @HttpCode(201)
  create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }

  @Get(':id')
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.usersService.findById(id);
  }
}
```

### DTO with class-validator

```typescript
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;

  @IsString()
  @MinLength(8)
  password: string;
}
```

### Service with repository or Prisma access

```typescript
@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async create(data: CreateUserDto) {
    const hashedPassword = await bcrypt.hash(data.password, 10);
    return this.prisma.user.create({
      data: { ...data, password: hashedPassword },
      select: { id: true, email: true, name: true },
    });
  }

  async findById(id: string) {
    const user = await this.prisma.user.findUnique({ where: { id } });
    if (user == null) {
      throw new NotFoundException('User not found');
    }
    return user;
  }
}
```

## Fastify Patterns

For more Fastify-specific guidance on plugin architecture, route schemas, hooks, decorators, and testing, see `references/fastify.md`.

### Route schema and handler

```typescript
fastify.post('/users', {
  schema: {
    body: userBodySchema,
    response: {
      201: userResponseSchema,
    },
  },
}, async (request, reply) => {
  const user = await userService.create(request.body);
  return reply.code(201).send(user);
});
```

## Database Patterns

For more Prisma-specific guidance on query shape, transactions, pagination, modeling, and operational pitfalls, see `references/prisma.md`.
For authentication and authorization patterns that often intersect with user/account persistence, see `references/auth.md`.

### Prisma best practices

```typescript
const users = await prisma.user.findMany({
  include: { posts: true, profile: true },
});

const safeUsers = await prisma.user.findMany({
  select: { id: true, email: true, name: true },
});

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

const page = await prisma.user.findMany({
  take: 20,
  skip: cursor ? 1 : 0,
  cursor: cursor ? { id: cursor } : undefined,
  orderBy: { createdAt: 'desc' },
});
```

### TypeORM repository pattern

```typescript
@EntityRepository(User)
export class UserRepository extends Repository<User> {
  async findWithPosts(id: string): Promise<User | null> {
    return this.findOne({
      where: { id },
      relations: ['posts'],
    });
  }
}
```

## Async Best Practices

```typescript
async function getDashboard(userId: string) {
  const [user, posts, notifications] = await Promise.all([
    getUser(userId),
    getUserPosts(userId),
    getNotifications(userId),
  ]);

  return { user, posts, notifications };
}

const results = await Promise.allSettled([
  fetchFromAPI1(),
  fetchFromAPI2(),
  fetchFromAPI3(),
]);

const successful = results
  .filter((r): r is PromiseFulfilledResult<Data> => r.status === 'fulfilled')
  .map((r) => r.value);

async function fetchWithTimeout(url: string, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

// Bad: async forEach does not await properly
items.forEach(async (item) => await process(item));

// Good: use Promise.all or for...of
await Promise.all(items.map((item) => process(item)));

for (const item of items) {
  await process(item);
}
```

## Validation with Zod

```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  password: z.string().min(8).regex(/[A-Z]/).regex(/[0-9]/),
});

type CreateUserInput = z.infer<typeof createUserSchema>;

const validate = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        status: 'error',
        code: 'VALIDATION_ERROR',
        errors: result.error.flatten().fieldErrors,
      });
    }

    req.body = result.data;
    next();
  };
};

router.post('/users', validate(createUserSchema), createUser);
```

## Security Patterns

For authentication, authorization, token/session handling, and protected route guidance, see `references/auth.md`.

```typescript
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import DOMPurify from 'isomorphic-dompurify';

app.use(helmet());

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
});
app.use('/api/', apiLimiter);

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
}));

const sanitized = DOMPurify.sanitize(userInput);
```

## Auth Patterns

For auth architecture, authorization checks, token/session handling, and protected route guidance, see `references/auth.md`.

### Auth middleware or guard goals

- authenticate once at the boundary
- attach typed user context
- fail closed on missing or invalid credentials
- separate authentication from authorization checks

## GraphQL Patterns

For broad GraphQL API design, schema evolution, resolver architecture, authorization, query safety, and cross-runtime review, pair with `graphql-api`. For Node-specific GraphQL implementation notes, see `references/graphql.md`.

### Resolver boundary rules

- keep resolvers thin and delegate business logic to services
- use loaders/batching on relation-heavy paths
- treat the schema as a public contract
- apply auth and policy checks consistently through context and services

## WebSocket Patterns

For WebSocket connection lifecycle, event contracts, rooms, auth, and scaling guidance, see `references/websockets.md`.

### Socket handler rules

- validate inbound event payloads
- authenticate connections and authorize room/resource access
- keep socket handlers thin and delegate business logic to services
- emit targeted events to rooms instead of broadcasting globally

## Logging Best Practices

For structured logging, metrics, traces, request correlation, health checks, and alerting guidance, see `references/observability.md`.

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: ['password', 'token', 'authorization'],
});

app.use((req, res, next) => {
  req.log = logger.child({
    requestId: req.headers['x-request-id'] ?? crypto.randomUUID(),
    path: req.path,
    method: req.method,
  });
  next();
});

logger.debug('Detailed debug info');
logger.info('User created', { userId: user.id });
logger.warn('Deprecated endpoint', { endpoint: req.path });
logger.error('Operation failed', { error, userId });
```

## Testing Patterns

For broader backend testing strategy across Express, NestJS, and Fastify, see `references/testing.md`.

```typescript
import request from 'supertest';
import { faker } from '@faker-js/faker';

describe('POST /api/users', () => {
  it('creates a new user', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', name: 'Test' })
      .expect(201);

    expect(response.body.data).toMatchObject({
      email: 'test@example.com',
      name: 'Test',
    });
  });

  it('returns 400 for invalid email', async () => {
    await request(app)
      .post('/api/users')
      .send({ email: 'invalid', name: 'Test' })
      .expect(400);
  });
});

const createUser = (overrides?: Partial<User>): User => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
  createdAt: new Date(),
  ...overrides,
});
```

## Quick Reference

```text
Errors      → Custom error classes + asyncHandler wrapper
Validation  → Zod or class-validator DTOs
Database    → Prisma/TypeORM with eager loading and narrow selects
Async       → Promise.all for parallel work; avoid async forEach
Security    → Helmet + CORS + rate limiting + sanitization
Logging     → Structured logging with Pino
Testing     → Supertest + factories
Auth        → JWT with Passport or NestJS guards
Config      → dotenv + typed config object
Routes      → RESTful conventions under /api/v1
Middleware  → Error handler registered last
Types       → Strict TypeScript, avoid any
```

## Common Pitfalls

1. Putting business logic in controllers instead of services.
2. Returning raw database records with sensitive fields like passwords.
3. Forgetting centralized async error handling in Express.
4. Using `forEach(async ...)` and assuming it waits.
5. Over-fetching from the database instead of using `select`.
6. Skipping validation at the API boundary.
7. Logging secrets, tokens, or full auth headers.
8. Writing route tests only and missing service-level behavior.

## Verification Checklist

- [ ] Routes validate input before reaching business logic
- [ ] Errors map to stable HTTP status codes and response shapes
- [ ] Services own core business logic
- [ ] Sensitive fields are excluded from API responses and logs
- [ ] Async work uses `Promise.all`, `Promise.allSettled`, or explicit sequencing
- [ ] Rate limiting, CORS, and security headers are configured
- [ ] Logging is structured and request-scoped where possible
- [ ] Tests cover success, validation failure, and not-found paths
