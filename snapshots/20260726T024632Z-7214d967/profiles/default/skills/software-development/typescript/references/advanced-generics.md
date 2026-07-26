# Advanced Generic Techniques

> **Scope:** Apply these patterns when the target repository needs reusable type-level behavior. Prefer the simplest type that preserves the public contract; do not introduce type-level complexity merely to remove a small amount of runtime duplication.

## When to Read This

Read this when designing reusable generic utilities, mapped/conditional types, template-literal APIs, or variadic tuple helpers.

## Start With Inference and Constraints

Use descriptive, `T`-prefixed parameters. Let call sites infer them whenever possible; add explicit type arguments only when inference cannot express the intended contract.

```ts
export function getProperty<TObject, TKey extends keyof TObject>(
	object: TObject,
	key: TKey,
): TObject[TKey] {
	return object[key];
}
```

A constraint should state the capability required by the implementation, not an unrelated nominal hierarchy.

```ts
type HasLength = { length: number };

export function withLength<TValue extends HasLength>(value: TValue): TValue {
	console.log(value.length);
	return value;
}
```

## Mapped Types

Mapped types transform every property of a known shape. Use them for a coherent, mechanical transformation—not to conceal an unclear data model.

```ts
export type Nullable<TObject> = {
	[TKey in keyof TObject]: TObject[TKey] | null;
};

export type Mutable<TObject> = {
	-readonly [TKey in keyof TObject]: TObject[TKey];
};

export type AsyncGetters<TObject> = {
	[TKey in keyof TObject as `get${Capitalize<string & TKey>}`]: () => Promise<TObject[TKey]>;
};
```

### Key Filtering and Remapping

```ts
export type FilterByValue<TObject, TValue> = {
	[TKey in keyof TObject as TObject[TKey] extends TValue ? TKey : never]: TObject[TKey];
};

export type Prefixed<TObject, TPrefix extends string> = {
	[TKey in keyof TObject as `${TPrefix}${Capitalize<string & TKey>}`]: TObject[TKey];
};
```

## Conditional Types and `infer`

Conditional types express a relationship between inputs and outputs. They distribute over unions when the checked value is a naked type parameter.

```ts
export type ArrayElement<TValue> = TValue extends readonly (infer TElement)[]
	? TElement
	: never;

export type FirstParameter<TFunction> = TFunction extends (
	first: infer TFirst,
	...rest: never[]
) => unknown
	? TFirst
	: never;

export type ExtractSuccessData<TResult> = TResult extends {
	success: true;
	data: infer TData;
}
	? TData
	: never;
```

To intentionally prevent distribution, wrap the checked value in a tuple:

```ts
export type ToArray<TValue> = TValue extends unknown ? TValue[] : never;
export type ToSingleArray<TValue> = [TValue] extends [unknown] ? TValue[] : never;

type Distributed = ToArray<string | number>; // string[] | number[]
type NonDistributed = ToSingleArray<string | number>; // (string | number)[]
```

## Template Literal Types

Use template literal types when a string format is a real public contract and runtime validation or construction exists at the boundary.

```ts
export type CssUnit = 'px' | 'em' | 'rem' | '%';
export type CssValue = `${number}${CssUnit}`;

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
export type Endpoint = '/users' | '/posts';
export type Route = `${HttpMethod} ${Endpoint}`;

export type PathSegment<TPath extends string> = TPath extends `${infer THead}.${infer TTail}`
	? THead | PathSegment<TTail>
	: TPath;
```

Do not mistake a compile-time template literal type for validation of untrusted strings. Parse or validate actual network and user input at runtime.

## Variadic Tuples

Variadic tuples preserve positional information for helpers that compose functions or arguments.

```ts
export type Concat<TLeft extends readonly unknown[], TRight extends readonly unknown[]> = [
	...TLeft,
	...TRight,
];

export type Prepend<TValue, TRest extends readonly unknown[]> = [TValue, ...TRest];
export type Append<TValues extends readonly unknown[], TValue> = [...TValues, TValue];
```

Keep variadic helpers small and test their inferred call-site behavior. If a generic `pipe` or `curry` signature is difficult to explain to its users, prefer a simpler explicit API.

## Built-in Utility Types

Prefer built-ins before authoring a duplicate utility.

| Utility | Use |
| --- | --- |
| `Partial<T>` / `Required<T>` | Make every property optional / required. |
| `Readonly<T>` | Readonly view of a shape when matching an external contract. |
| `Pick<T, K>` / `Omit<T, K>` | Data projection; question single-method DI seams. |
| `Record<K, V>` | Exhaustive finite mappings or dictionary-like data. |
| `Exclude<T, U>` / `Extract<T, U>` | Filter an upstream union you do not own. |
| `NonNullable<T>` | Remove nullish members from a type. |
| `Parameters<T>` / `ReturnType<T>` | Derive a function contract from its owner. |
| `ConstructorParameters<T>` / `InstanceType<T>` | Derive a constructor contract when classes are framework-required. |
| `Awaited<T>` | Unwrap promise-like values. |
| `NoInfer<T>` | Prevent an argument from influencing inference when that is deliberate. |

## Assertion Functions

Assertion functions narrow a value for code after the call. Use them to enforce trusted internal invariants, not as a substitute for validating untrusted input.

```ts
export function assertDefined<TValue>(
	value: TValue | undefined,
	message: string,
): asserts value is TValue {
	if (value === undefined) throw new Error(message);
}
```

For network, file, or user input, use the repository's runtime schema validator instead.