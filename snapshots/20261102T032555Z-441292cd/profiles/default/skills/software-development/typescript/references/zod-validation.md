# Zod Runtime Validation

> **Scope:** Use this reference only when Zod is installed and selected by the target repository. It is an alternative to—not an instruction to replace—Arktype, TypeBox, Valibot, or another established runtime schema library.

## When to Read This

Read this when defining Zod schemas at a network, file, environment, form, or persistence boundary and deriving TypeScript types from those schemas.

## Schema First, Type Inferred

A runtime schema should own the corresponding TypeScript shape. Use the same identifier in value and type positions when that improves readability.

```ts
import { z } from 'zod';

export const User = z.object({
	id: z.string().uuid(),
	name: z.string().min(1).max(100),
	email: z.string().email(),
	role: z.enum(['user', 'admin']),
});

export type User = z.infer<typeof User>;
```

Do not maintain a hand-written `User` shape beside a schema that already owns it.

## Derive Input Schemas

Build related boundary schemas from the source schema to avoid drift.

```ts
export const CreateUser = User.omit({ id: true });
export type CreateUser = z.infer<typeof CreateUser>;

export const UpdateUser = CreateUser.partial();
export type UpdateUser = z.infer<typeof UpdateUser>;
```

## Validate `unknown` at the Boundary

Use `parse` when a thrown validation error is appropriate for the local error-handling model. Use `safeParse` when callers need an explicit success/failure branch.

```ts
export function parseUser(input: unknown): User {
	return User.parse(input);
}

export function tryParseUser(input: unknown) {
	return User.safeParse(input);
}
```

Never cast untrusted input to the inferred type. Validation is the point at which `unknown` becomes trusted data.

## Format Errors Deliberately

Preserve structured issue data for logs or programmatic callers. Convert it to a stable response shape only at an application/API boundary.

```ts
export function formatZodIssues(error: z.ZodError): Record<string, string[]> {
	const messagesByPath: Record<string, string[]> = {};

	for (const issue of error.issues) {
		const path = issue.path.join('.') || 'form';
		(messagesByPath[path] ??= []).push(issue.message);
	}

	return messagesByPath;
}
```

## Environment Configuration

Validate environment configuration once at application startup. Do not log the resulting secret values.

```ts
const Environment = z.object({
	NODE_ENV: z.enum(['development', 'production', 'test']),
	PORT: z.coerce.number().int().positive().default(3000),
	DATABASE_URL: z.string().url(),
});

export function loadEnvironment(input: unknown) {
	return Environment.parse(input);
}
```

Keep provider-specific requirements and secrets in the owning application or deployment documentation.