# Result and Error Boundaries

> **Scope:** Use the error model already established by the target repository. This reference helps choose a typed result or exception boundary; it does not require either model everywhere.

## When to Read This

Read this when a function can fail in an expected, recoverable way and its caller needs a typed failure path.

## Typed Results

A discriminated result makes success and expected failure explicit without a cast or implicit sentinel value.

```ts
export type Result<TData, TError> =
	| { success: true; data: TData }
	| { success: false; error: TError };

export function ok<TData>(data: TData): Result<TData, never> {
	return { success: true, data };
}

export function err<TError>(error: TError): Result<never, TError> {
	return { success: false, error };
}
```

Use `Result` for anticipated domain outcomes: validation failures, conflicts, unavailable dependencies, or a missing record when absence is part of normal flow. Let unexpected programmer errors surface rather than converting every exception into an unhelpful broad union.

```ts
export type InvalidEmail = { name: 'InvalidEmail'; message: string };

export function normalizeEmail(input: string): Result<string, InvalidEmail> {
	const value = input.trim().toLowerCase();
	if (!value.includes('@')) {
		return err({ name: 'InvalidEmail', message: 'A valid email address is required.' });
	}
	return ok(value);
}
```

## Exception Boundaries

Factory functions remain the default for application objects. A subclass of `Error` is a deliberate exception when a framework or boundary requires `instanceof` behavior and stack semantics.

```ts
export class ValidationError extends Error {
	readonly name = 'ValidationError';

	constructor(
		message: string,
		readonly fields: Record<string, readonly string[]>,
	) {
		super(message);
		Error.captureStackTrace?.(this, ValidationError);
	}
}

export function isValidationError(error: unknown): error is ValidationError {
	return error instanceof ValidationError;
}
```

Keep the class hierarchy shallow. Do not use exceptions as a substitute for validating `unknown` input or for routine control flow.

## Public Response Shapes

Do not use a type projection as the only protection against leaking fields. Select or transform the actual runtime object, then publish the resulting explicit response contract.

```ts
type InternalUser = {
	id: string;
	email: string;
	passwordHash: string;
	internalNotes: string;
};

export type PublicUser = Pick<InternalUser, 'id' | 'email'>;

export function toPublicUser(user: InternalUser): PublicUser {
	return { id: user.id, email: user.email };
}
```

The transformation makes the runtime behavior match the advertised type.