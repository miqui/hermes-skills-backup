---
name: playwright-testing
description: "Use when adding, reviewing, debugging, or maintaining Playwright browser automation, end-to-end tests, REST API tests, and GraphQL API tests for web apps and services, including setup, selectors, fixtures, auth state, request contexts, traces, CI, and converting exploratory findings into repeatable regression coverage."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [playwright, e2e, browser, rest-api, graphql, api-testing, testing, qa, automation, ci]
    related_skills: [dogfood, chat-app-validation, test-driven-development, node-backend, bun-backend, openapi-specification, graphql-api, api-governance]
---

# Playwright Testing

## Overview

Use this skill for Playwright-based browser automation, end-to-end testing, and HTTP API testing. It covers the handoff from exploratory QA to repeatable tests, plus practical Playwright defaults for selectors, fixtures, authentication state, `APIRequestContext`, REST endpoints, GraphQL operations, traces, screenshots, videos, CI, and debugging.

Playwright is the right tool when the desired output is a **regression test that can be rerun** in local development or CI. Hermes browser tools are still better for quick exploratory navigation, ad-hoc visual inspection, and evidence collection. A strong workflow uses both: explore with `dogfood`, then encode stable behaviors with Playwright. For API contracts, pair this skill with `openapi-specification` for REST/OpenAPI or `graphql-api` for GraphQL schema and resolver concerns.

## When to Use

Use this skill when the task involves:
- Setting up Playwright in a JavaScript, TypeScript, Node.js, Bun, or frontend repo
- Writing browser E2E tests for navigation, forms, auth, search, checkout, dashboards, chat apps, or multi-step user flows
- Writing REST API tests with Playwright's `request` fixture or `APIRequestContext`
- Writing GraphQL operation tests over HTTP with realistic documents, variables, auth contexts, and error assertions
- Combining API setup/teardown with browser assertions, such as creating test data through REST/GraphQL before checking the UI
- Converting a manually reproduced bug into a regression test
- Reviewing Playwright test quality, selector strategy, API assertion quality, fixture design, or CI configuration
- Debugging flaky Playwright tests, API timeouts, request-context issues, browser install issues, traces, screenshots, or videos
- Deciding whether a behavior should be covered by unit, integration, API, or E2E tests

Do **not** use this skill as the primary path when:
- The user only wants one-off exploratory QA with screenshots and a bug report — use `dogfood`
- The API contract itself is unclear or needs design/review first — use `openapi-specification`, `openapi-api-designer`, `graphql-api`, or `api-governance` as appropriate
- The bug is clearly isolated to backend logic with no browser or HTTP contract relevance — use the relevant backend/testing skill first
- The repo already has a non-Playwright API/E2E framework and the user did not ask to migrate
- The task would require production-impacting actions such as real purchases, emails, account changes, destructive writes, or testing against production APIs without explicit scope approval

## Tool Choice: Hermes Browser vs Playwright

| Need | Preferred tool |
| --- | --- |
| Discover bugs interactively | `dogfood` + browser tools |
| Capture visual evidence for a report | `browser_vision` screenshots |
| Validate a local chat/UI flow end-to-end once | `chat-app-validation` |
| Create repeatable regression coverage | Playwright tests |
| Test REST endpoints over HTTP | Playwright `request` fixture / `APIRequestContext` |
| Test GraphQL operations over HTTP | Playwright `request.post('/graphql', { data })` plus GraphQL-specific assertions |
| Set up API state before UI checks | Playwright API request context + browser page |
| Run browser checks in CI | Playwright tests |
| Debug deterministic browser failures | Playwright trace viewer, screenshots, videos |
| Explore unknown UI affordances | Hermes browser snapshot/vision before writing tests |

## Setup Discovery

Before adding anything, inspect the repo:
1. Package manager: `package.json`, lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `bun.lock`)
2. Existing test scripts and CI workflows
3. Framework conventions: Next.js, Vite, Remix, SvelteKit, Astro, Rails frontend, etc.
4. Existing Playwright files: `playwright.config.*`, `tests/e2e/**`, `tests/api/**`, `e2e/**`, `api/**`, `*.spec.ts`
5. App startup command and required environment variables
6. Whether tests should hit a dev server, a preview build, a deployed URL, or a dedicated API base URL
7. REST contracts: OpenAPI files, route declarations, API docs, generated clients, or contract tests
8. GraphQL contracts: schema files, generated types, operation documents, persisted-query setup, or codegen config
9. Existing auth/test-data strategy for API tests and browser tests

Prefer the repo's existing package manager and style. Do not introduce a new package manager just for Playwright.

## Installation and Common Commands

Use the project package manager. Typical commands:

```bash
# npm
npm init playwright@latest
npx playwright test
npx playwright install
npx playwright test --trace on
npx playwright show-report

# pnpm
pnpm create playwright
pnpm exec playwright test
pnpm exec playwright install
pnpm exec playwright test --trace on
pnpm exec playwright show-report

# yarn
yarn create playwright
yarn playwright test
yarn playwright install
yarn playwright test --trace on
yarn playwright show-report

# bun, when the repo intentionally uses Bun
bunx playwright test
bunx playwright install
bunx playwright test --trace on
```

Browser binaries are large. Install them only when needed for local/CI execution, and avoid repeatedly deleting the Playwright browser cache unless the task is specifically about disk cleanup or broken browsers.

## Recommended Project Shape

Common TypeScript layout:

```text
playwright.config.ts
tests/
  e2e/
    smoke.spec.ts
    auth.spec.ts
    regression-issue-name.spec.ts
  api/
    rest/
      health.spec.ts
      orders.spec.ts
    graphql/
      project-query.spec.ts
      create-project-mutation.spec.ts
  fixtures/
    test.ts
    api.ts
  pages/
    login-page.ts
```

Keep E2E tests separate from unit tests unless the repo already has a different convention. Keep API-only Playwright tests separate from browser E2E tests when the suite grows. Use descriptive filenames by feature, resource, operation, or user journey, not by implementation component.

## REST API Testing with Playwright

Playwright can test HTTP APIs without launching a browser by using the built-in `request` fixture or an explicit `APIRequestContext`. Use this for REST smoke tests, contract-adjacent behavior tests, setup/teardown helpers for UI tests, and regression tests for API bugs.

Pair REST API testing with `openapi-specification` when an OpenAPI contract exists or should exist. Playwright should verify live behavior; OpenAPI validation should verify contract shape, schemas, examples, status codes, and compatibility.

### Basic REST test

```ts
import { test, expect } from '@playwright/test';

test('GET /health returns healthy status', async ({ request }) => {
  const response = await request.get('/health');

  expect(response.ok()).toBeTruthy();
  expect(response.status()).toBe(200);
  await expect(response).toBeOK();

  const body = await response.json();
  expect(body).toEqual(expect.objectContaining({ status: 'ok' }));
});
```

### REST best practices

- Configure `baseURL` in Playwright config or a dedicated request context; avoid repeating absolute URLs in every test.
- Keep API credentials in environment variables or CI secrets; never commit tokens, cookies, storage state, or real session files.
- Use `extraHTTPHeaders` for stable headers such as `Accept`, API version, tenant, correlation id, or auth.
- Assert status code, content type when relevant, and body shape. Do not stop at `response.ok()` for behavior-critical endpoints.
- Test negative cases: invalid input, missing auth, unauthorized actor, not found, conflict, rate/validation limits, and malformed JSON.
- Keep writes scoped to test accounts, test tenants, local databases, or disposable fixtures. Avoid production APIs unless the user explicitly approves the scope.
- Clean up created resources through API teardown or isolated test data. Make tests idempotent where possible.
- Prefer stable semantic assertions over snapshotting entire volatile responses with timestamps, random IDs, or ordering noise.
- For OpenAPI-backed services, validate representative responses against the contract when the repo has tooling for it.
- Separate API-only smoke/contract-adjacent tests from full browser E2E tests so fast API failures are easy to diagnose.

### Explicit API request context

Use an explicit context when tests need a different API host, shared headers, or setup/teardown outside the browser page context:

```ts
import { test, expect, type APIRequestContext } from '@playwright/test';

let api: APIRequestContext;

test.beforeAll(async ({ playwright }) => {
  const token = process.env.API_TOKEN;
  if (!token) {
    throw new Error('API_TOKEN is required for API tests');
  }

  const authHeaderName = 'Authorization';
  api = await playwright.request.newContext({
    baseURL: process.env.API_BASE_URL ?? 'http://localhost:3000/api',
    extraHTTPHeaders: {
      Accept: 'application/json',
      [authHeaderName]: ['Bearer', token].join(' '),
    },
  });
});

test.afterAll(async () => {
  await api.dispose();
});

test('creates and fetches an order', async () => {
  const create = await api.post('/orders', {
    data: { sku: 'TEST-SKU', quantity: 1 },
  });
  expect(create.status()).toBe(201);
  const created = await create.json();

  const fetch = await api.get(`/orders/${created.id}`);
  await expect(fetch).toBeOK();
  expect(fetch.headers()['content-type']).toContain('application/json');
  expect(await fetch.json()).toEqual(expect.objectContaining({
    id: created.id,
    sku: 'TEST-SKU',
    quantity: 1,
  }));
});
```

Security note: in real test code, skip or fail fast with a clear message when a required token is absent, without printing the token.

## GraphQL API Testing with Playwright

GraphQL tests use the same Playwright HTTP primitives, usually by POSTing to `/graphql` with `{ query, variables, operationName }`. Pair this section with `graphql-api` for schema design, resolver boundaries, authorization, nullability, pagination, query cost, and schema evolution.

### Basic GraphQL query test

```ts
import { test, expect } from '@playwright/test';

const ProjectQuery = `#graphql
  query Project($id: ID!) {
    project(id: $id) {
      id
      name
      owner {
        id
        displayName
      }
    }
  }
`;

test('Project query returns project and owner', async ({ request }) => {
  const response = await request.post('/graphql', {
    data: {
      operationName: 'Project',
      query: ProjectQuery,
      variables: { id: 'project-test-1' },
    },
  });

  await expect(response).toBeOK();
  const body = await response.json();

  expect(body.errors).toBeUndefined();
  expect(body.data.project).toEqual(expect.objectContaining({
    id: 'project-test-1',
    name: expect.any(String),
  }));
  expect(body.data.project.owner).toEqual(expect.objectContaining({
    id: expect.any(String),
    displayName: expect.any(String),
  }));
});
```

### GraphQL best practices

- Always send named operations with `operationName`; unnamed ad-hoc documents make traces, logs, persisted queries, and failure reports harder to understand.
- Keep operation documents realistic. Exercise parsing, validation, variables, auth context, resolver wiring, and serialization together.
- Assert both HTTP-level behavior and GraphQL-level behavior. A GraphQL response can be HTTP 200 and still contain `errors`.
- For success cases, assert `errors` is absent and `data` has the expected shape.
- For expected business errors, assert stable error codes/paths/extensions rather than brittle error message prose.
- Test auth and tenancy through direct object queries and nested access paths; clients can send valid operations outside the UI path.
- Cover nullability and partial-result behavior deliberately. A non-null resolver error may null out parent fields.
- Cover pagination boundaries: first page, after cursor, empty page, maximum page size, and stable ordering.
- Include N+1-sensitive relation paths in operation tests when feasible; pair with server-side query-count or loader assertions if the repo supports them.
- Test query depth/cost rejection if the API exposes complexity limits.
- Do not rely on introspection in production-like tests unless the environment intentionally allows it.
- Use generated GraphQL types/documents when the repo has codegen; avoid duplicating stale operation strings when a typed operation source already exists.

### GraphQL mutation test pattern

```ts
const CreateProjectMutation = `#graphql
  mutation CreateProject($input: CreateProjectInput!) {
    createProject(input: $input) {
      project { id name }
      userErrors { field message code }
    }
  }
`;

test('CreateProject mutation creates a project', async ({ request }) => {
  const response = await request.post('/graphql', {
    data: {
      operationName: 'CreateProject',
      query: CreateProjectMutation,
      variables: {
        input: { name: `Test Project ${Date.now()}` },
      },
    },
  });

  await expect(response).toBeOK();
  const body = await response.json();

  expect(body.errors).toBeUndefined();
  expect(body.data.createProject.userErrors).toEqual([]);
  expect(body.data.createProject.project).toEqual(expect.objectContaining({
    id: expect.any(String),
    name: expect.stringContaining('Test Project'),
  }));
});
```

## Combining API and Browser Tests

Use API calls for setup or postcondition checks when they make the browser test clearer and faster, but keep the user-visible assertion in the browser when the feature is a UI behavior.

Good uses:
- Create a test user, cart, issue, order, or project through REST/GraphQL before navigating to the UI
- Clean up data after a browser journey
- Verify that a UI action persisted server-side
- Seed GraphQL fixtures for a chat/tool-result rendering test

Avoid:
- Replacing the browser assertion with only an API assertion when the bug was in rendering or hydration
- Hiding important user actions behind setup APIs so the E2E test no longer covers the journey
- Sharing state across tests in a way that creates order dependence

Example:

```ts
test('created order appears in the orders UI', async ({ request, page }) => {
  const create = await request.post('/api/orders', {
    data: { sku: 'TEST-SKU', quantity: 1 },
  });
  expect(create.status()).toBe(201);
  const order = await create.json();

  await page.goto('/orders');
  await expect(page.getByRole('link', { name: order.id })).toBeVisible();
});
```

## Writing Good Playwright Tests

### Prefer user-visible locators

Favor locators that match how users experience the app:

```ts
await page.getByRole('button', { name: 'Submit' }).click();
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
await page.getByLabel('Email').fill('user@example.com');
await page.getByPlaceholder('Search').fill('coffee');
await page.getByTestId('cart-total').toContainText('$12.00');
```

Selector priority:
1. `getByRole` with accessible name
2. `getByLabel`, `getByPlaceholder`, `getByText`, `getByAltText`, `getByTitle`
3. `getByTestId` for stable app-specific hooks
4. CSS selectors only when the UI has no semantic target
5. Avoid brittle XPath, generated class names, nth-child chains, and text that changes frequently

If the only possible selector is brittle, consider improving app accessibility or adding a stable test id as part of the change.

### Use web-first assertions

Use Playwright's auto-waiting assertions rather than manual sleeps:

```ts
await expect(page.getByRole('status')).toHaveText(/saved/i);
await expect(page.getByRole('button', { name: 'Checkout' })).toBeEnabled();
await expect(page).toHaveURL(/\/orders\/\d+$/);
```

Avoid:

```ts
await page.waitForTimeout(1000); // Flaky; use an assertion on the real condition instead.
```

### Test behavior, not implementation

Good E2E tests assert visible outcomes:
- A user can sign in
- Search results appear
- A cart total updates
- A chat tool-result card renders
- A form shows validation feedback

Weak E2E tests assert internal details:
- React state variable names
- CSS implementation classes
- Network calls that do not affect visible behavior
- Database rows without validating the browser contract

## Fixtures and Test Isolation

Playwright Test gives each test an isolated `page` fixture backed by a fresh browser context. Preserve that isolation unless there is a deliberate reason to share state.

Use fixtures when setup is repeated and meaningful:

```ts
import { test as base, expect } from '@playwright/test';

class LoginPage {
  constructor(private readonly page) {}
  async goto() {
    await this.page.goto('/login');
  }
}

type Fixtures = { loginPage: LoginPage };

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
});

export { expect };
```

Fixture guidance:
- Keep fixtures small and explicit
- Use them for setup that many tests share
- Avoid hiding the user journey so deeply that test intent disappears
- Put cleanup in fixtures when the setup creates data
- Do not make tests order-dependent

## Authentication State

For authenticated flows, prefer a setup project or explicit helper that logs in once and stores a scoped auth state for test use. Keep auth state local, ignored by git, and environment-specific.

Guidelines:
- Do not commit real user session storage
- Use test accounts, seeded users, or local fixtures
- Keep auth setup deterministic and documented
- Separate login coverage from tests that merely require an authenticated session
- Recreate auth state when credentials, base URL, or storage schema changes

## Converting Bugs into Regression Tests

When a manual QA session finds a bug:
1. Record the exact reproduction steps, URL, expected behavior, actual behavior, and screenshot/console evidence
2. Add a Playwright test that reproduces the bug before fixing it when practical
3. Run the test and confirm it fails for the expected reason
4. Implement the minimal fix
5. Re-run the specific test, then the relevant E2E suite
6. Keep the test named after the user-visible behavior, not the internal bug cause

Pair with `test-driven-development` when the bug fix changes production code.

## Local App Startup

A stable Playwright config should define how the app starts for tests when possible:

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

Adapt the command to the repo (`npm`, `pnpm`, `yarn`, or `bun`). If the app requires build output, use the repo's preview/start command instead of dev mode.

## Debugging Playwright

Use the least noisy debug artifact that answers the question:

```bash
# Open headed browser
npx playwright test --headed

# Debug one test interactively
npx playwright test tests/e2e/example.spec.ts --debug

# Capture full trace for a run
npx playwright test --trace on

# Open an existing trace archive
npx playwright show-trace path/to/trace.zip

# Run only one browser/project
npx playwright test --project=chromium

# Run one test by title
npx playwright test -g "user can search"
```

Debugging sequence for flakes:
1. Re-run the specific test locally
2. Inspect trace, screenshot, and video
3. Replace sleeps with assertions on the real condition
4. Remove order dependence and shared state
5. Stabilize test data and network assumptions
6. Only increase timeouts after identifying why the default was insufficient

## CI Guidance

CI should install dependencies, install Playwright browsers, run tests, and upload report artifacts on failure.

General rules:
- Cache package manager dependencies, not blindly every browser artifact unless the CI image/cache policy supports it
- Run a small smoke suite first if full E2E is expensive
- Upload `playwright-report/`, `test-results/`, traces, screenshots, and videos as artifacts
- Use retries sparingly and treat retries as a signal of flakiness, not a fix
- Prefer `trace: 'on-first-retry'` for routine CI; use `--trace on` for focused debugging
- Keep production credentials out of E2E tests; use test environments and test accounts

## Page Objects: Use Sparingly

Page objects are useful when they clarify repeated user interactions. They are harmful when they hide assertions or reproduce the app's implementation hierarchy.

Good page object methods:
- `loginAsTestUser()`
- `searchFor(query)`
- `addItemToCart(name)`
- `expectOrderTotal(amount)`

Poor page object methods:
- `clickButton1()`
- `setInternalState()`
- `waitForApp()` with a sleep
- wrappers around every Playwright API call with no domain meaning

## Accessibility as Testability

If Playwright tests cannot find elements by role, label, or visible name, that often reveals an accessibility issue. Prefer improving semantic markup over adding fragile selectors. When adding `data-testid`, use it for app-specific stable targets that do not have a natural accessible role or label.

## Common Pitfalls

1. **Writing E2E tests for everything.** Browser tests are expensive. Cover critical user journeys and regression-prone paths; leave pure logic to unit tests.
2. **Using sleeps to fix flakes.** Replace `waitForTimeout` with a web-first assertion for the real condition.
3. **Brittle selectors.** Avoid generated classes, DOM-depth selectors, and text likely to change.
4. **Shared mutable state.** Tests should not depend on execution order or data left by previous tests.
5. **Committing auth state or secrets.** Storage state and credentials must be local/CI-secret managed and ignored by git.
6. **Ignoring traces.** Trace artifacts usually explain CI-only failures faster than guessing.
7. **Only testing happy paths.** Include validation errors, empty states, loading states, and permission failures for critical flows.
8. **Over-abstracting page objects.** If the test no longer reads like a user journey, the abstraction is too heavy.
9. **Running against production accidentally.** Make `baseURL` explicit and confirm destructive flows are disabled or scoped to test data.
10. **Installing browsers repeatedly without need.** Browser downloads are large; install deliberately and cache appropriately in CI.
11. **Treating API tests as contract validation by default.** Playwright verifies runtime behavior; use OpenAPI/GraphQL tooling for full schema/contract compatibility checks when available.
12. **Only asserting HTTP 200 for GraphQL.** GraphQL can return HTTP 200 with `errors`; assert both transport and GraphQL payload semantics.
13. **Leaking API tokens while debugging.** Check token presence as boolean and never print headers, cookies, storage state, or env files.
14. **Using shared API-created data without cleanup.** API tests that create data must isolate, clean up, or use disposable fixtures to avoid order dependence and polluted environments.

## Verification Checklist

- [ ] Repo package manager and existing test conventions were discovered before changes
- [ ] Playwright setup uses the repo's package manager and scripts
- [ ] Tests target user-visible behavior, critical flows, or explicit REST/GraphQL API behavior
- [ ] REST API tests assert status codes, meaningful headers/content type where relevant, and stable response-body semantics
- [ ] GraphQL tests assert both HTTP transport success/failure and GraphQL `data` / `errors` semantics
- [ ] API tests cover representative success, validation failure, auth failure, authorization failure, not-found/conflict, and boundary cases where applicable
- [ ] API test data is isolated, disposable, cleaned up, or idempotent
- [ ] API credentials, tokens, cookies, storage state, traces, screenshots, and videos are ignored or handled as CI artifacts/secrets where appropriate
- [ ] Locators prefer roles, labels, text, or stable test ids over brittle CSS/XPath
- [ ] Assertions use Playwright auto-waiting expectations, not sleeps
- [ ] Tests are isolated and order-independent
- [ ] REST/OpenAPI work is paired with contract validation tooling when the repo has an OpenAPI spec or validator
- [ ] GraphQL work is paired with `graphql-api` guidance for schema, auth, nullability, pagination, and query-cost concerns
- [ ] Auth state, credentials, screenshots, videos, and traces are ignored or handled as CI artifacts where appropriate
- [ ] The specific test was run and the result was reported
- [ ] Relevant suite or smoke suite was run after fixes
- [ ] CI config uploads useful Playwright artifacts on failure when CI changes were made

## One-Shot Recipes

### Recipe: Convert a dogfood bug into a Playwright regression
1. Load `dogfood` output: URL, reproduction steps, expected/actual behavior, screenshots, and console errors
2. Add a test under the repo's E2E test directory using user-visible selectors
3. Run the single test and confirm it fails for the expected user-visible reason
4. Fix the app behavior
5. Run the single test again, then the E2E smoke suite
6. Report the test path and exact commands/results

### Recipe: Add Playwright to an existing frontend repo
1. Inspect package manager, framework, test scripts, and CI
2. Run the package-manager-appropriate Playwright initializer only if the repo has no existing setup
3. Configure `baseURL`, `webServer`, trace/screenshot/video policy, and one browser project first
4. Add one smoke test for a stable critical journey
5. Run browser installation if needed, then run the smoke test
6. Add CI only after local execution is green

### Recipe: Add Playwright REST API coverage
1. Inspect existing API tests, OpenAPI files, route definitions, auth setup, and test data strategy
2. Configure `baseURL` and shared headers through Playwright config or `APIRequestContext`
3. Add one success-path test for a stable endpoint and at least one failure-path test for validation or auth
4. Assert status, content type where relevant, and stable response-body semantics
5. Keep writes isolated and clean up created resources
6. Run the API test file directly, then the relevant API smoke suite
7. If an OpenAPI contract exists, run the repo's contract validator and report both Playwright and contract results

### Recipe: Add Playwright GraphQL API coverage
1. Inspect schema, operation documents, generated types, auth context, and query-cost/pagination rules
2. Use named operations with realistic variables and explicit `operationName`
3. Add one success-path query or mutation test that asserts HTTP success, no unexpected `errors`, and expected `data`
4. Add failure-path coverage for invalid input, unauthorized access, expected user errors, or query-cost/depth rejection
5. Cover pagination/nullability boundaries when the changed operation depends on them
6. Run the GraphQL Playwright test directly, then the relevant API smoke suite
7. Pair with `graphql-api` for schema/resolver review if the test exposes contract or resolver-design questions

### Recipe: Debug a flaky CI-only failure
1. Pull the failing test name, browser project, trace, screenshot, and video artifacts
2. Re-run the exact test locally with the same project
3. Open the trace and identify the first wrong assumption
4. Fix selectors, waits, data setup, or isolation; do not paper over with sleeps
5. Re-run the single test repeatedly enough to build confidence, then the relevant suite
