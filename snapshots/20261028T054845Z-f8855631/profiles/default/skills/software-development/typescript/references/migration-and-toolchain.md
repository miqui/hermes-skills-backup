# Migration and Toolchain Selection

> **Scope:** Inspect the repository before changing its compiler, module, package-manager, linter, formatter, or test-runner configuration. This is a decision guide, not a mandate to adopt pnpm, Vite, Vitest, Prettier, or a particular Node version.

## When to Read This

Read this when incrementally migrating JavaScript to TypeScript, moving CommonJS to ESM, or deciding which TypeScript configuration shape matches an existing project.

## Incremental JavaScript Migration

Prefer a reversible, file-by-file migration over a large rename-only conversion.

1. **Prepare:** add a `tsconfig` that includes the intended source files. During the transition, `allowJs: true` and `checkJs: false` can permit JavaScript and TypeScript to coexist.
2. **Convert behaviorally isolated modules:** rename one module, resolve its errors, and run the relevant tests before proceeding.
3. **Use JSDoc as a bridge:** type JavaScript that cannot yet be converted, especially public functions and data boundaries.
4. **Tighten in stages:** enable `noImplicitAny`, then null checking, then `strict`; consider `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` after the codebase is ready.
5. **Remove transition settings:** do not leave `allowJs`, broad suppressions, or `skipLibCheck` enabled merely because they made the first migration pass easier.

```js
/**
 * @template TValue
 * @param {TValue[]} values
 * @returns {TValue | undefined}
 */
export function first(values) {
	return values[0];
}
```

## CommonJS to ESM

Adopt ESM only after checking package consumers, test runners, bundlers, and Node/runtime support.

- Set `"type": "module"` in `package.json` when the package is intentionally ESM.
- Replace `require`/`module.exports` with `import`/`export`.
- For Node-aware ESM resolution, use `.js` runtime extensions in relative TypeScript imports when the project’s module-resolution mode requires them.
- Do not apply `.js` extension rules to bundler-managed aliases or a repository whose existing module strategy differs.

## Choose the Configuration Shape From the Runtime

| Project type | Typical direction | Verify first |
| --- | --- | --- |
| Browser/bundler application | `moduleResolution: "bundler"`, DOM libraries, `jsx: "react-jsx"` only for React | Bundler, framework, browser targets, alias support |
| Node ESM service/library | `module` and `moduleResolution` set to `NodeNext` | Node version, package `type`, publish format, relative-import rules |
| Library | Declarations and maps may be emitted | Package exports, bundler/transpiler, consumer expectations |
| Monorepo | Project references may help, but add only when the build graph needs them | Workspace scripts, package boundaries, build cache strategy |

Use the templates in this skill only as starting points. Preserve existing project settings where they encode runtime compatibility.

## Toolchain Checks

Before adding or changing a tool, inspect:

- `package.json` scripts and package-manager lockfile
- TypeScript version and existing `tsconfig*` files
- the active Node/runtime version and deployment target
- lint, formatting, and test configuration
- CI commands and generated-output expectations

Do not copy a configuration just because it is newer or labeled “enterprise.” A strict compiler option or type-aware ESLint rule is valuable only if its runtime assumptions, performance cost, and migration impact are understood.