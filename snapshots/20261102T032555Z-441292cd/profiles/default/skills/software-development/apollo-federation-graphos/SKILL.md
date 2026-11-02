---
name: apollo-federation-graphos
description: "Use when working with Apollo Federation 2, Apollo Server v4 subgraphs, Apollo Router, the Rover CLI, or GraphOS/Apollo Studio — composing, running, testing, publishing, or operating a federated GraphQL graph on the Apollo vendor stack. Delegates vendor-neutral GraphQL schema/resolver/authorization/testing design to graphql-api and covers only Apollo-specific mechanics: Federation 2 directives and entities, Apollo Server v4 subgraph implementation, Apollo Router local config/CORS, Rover check/compose/publish workflows, GraphOS graph refs and Studio, CI composition gates, and secret-safe APOLLO_KEY/APOLLO_GRAPH_REF handling."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [graphql, apollo, federation, graphos, apollo-router, apollo-server, rover, subgraph, supergraph]
    related_skills: [graphql-api, node-backend, playwright-testing, typescript, secure-agent-skills, skill-security-review-gates]
---

# Apollo Federation & GraphOS

## Overview

This skill covers the **Apollo vendor stack** for federated GraphQL: Apollo Federation 2 spec directives, Apollo Server v4 as a subgraph runtime, Apollo Router as the gateway/composition runtime, the Rover CLI for schema checks and publication, and GraphOS/Apollo Studio as the graph registry and observability plane.

It deliberately does **not** re-teach GraphQL fundamentals. Schema design, resolver architecture, nullability, pagination, DataLoader/N+1 patterns, authorization placement, error modeling, query-cost controls, and operation-level testing are all covered by `graphql-api` — load that skill first for anything vendor-neutral and treat this skill as the Apollo-specific layer on top of it. If a task is "design a GraphQL mutation" with no federation/Apollo tooling involved, this skill does not apply; use `graphql-api` alone.

Apollo tooling touches two categories of risk that deserve explicit handling:

1. **Local, read-only, reversible** work: inspecting subgraph schemas, running `rover ... check`, composing a supergraph locally, running the Router against a local supergraph file, reading Studio dashboards.
2. **Remote, mutating, hard-to-reverse** work: `rover subgraph publish`, promoting/creating variants, editing contracts, rotating or creating graph API keys in GraphOS.

Default to category 1. Never perform category 2 without the user explicitly asking for that specific mutation, naming the graph ref/variant, and confirming they want it done now.

## When to Use

- Reviewing or writing `@key`, `@shareable`, `@override`, `@requires`, `@provides`, `@external`, `@inaccessible`, `@tag`, `@interfaceObject`, or `@composeDirective` usage in a subgraph schema.
- Implementing or reviewing an Apollo Server v4 subgraph (`buildSubgraphSchema`, `__resolveReference`, entity resolvers).
- Configuring or running Apollo Router locally (`router.yaml`, CORS, header propagation, supergraph loading).
- Running `rover subgraph check` or `rover supergraph compose` before a merge or release.
- Preparing (but not necessarily executing) a `rover subgraph publish` step.
- Interpreting GraphOS/Apollo Studio graph refs, variants, checks, and operation metrics.
- Testing a composed federated graph end-to-end through the Router rather than against individual subgraphs.
- Adding or reviewing CI jobs that gate merges on federation composition checks.
- Handling `APOLLO_KEY` / `APOLLO_GRAPH_REF` in scripts, CI config, or `.env` files without leaking them.

Don't use this skill alone for:

- Generic schema/resolver/authorization/pagination/testing design — use `graphql-api` (this skill assumes that foundation).
- Node.js server architecture unrelated to the subgraph layer — pair with `node-backend`.
- Browser/e2e test authoring mechanics — pair with `playwright-testing`.
- Non-Apollo federation-capable runtimes (GraphQL Yoga + Envelop, Mercurius federation, etc.) — see **Vendor-Runtime Roadmap** below; do not stretch this skill to cover them.

## Relationship to `graphql-api`

| Concern | Skill |
|---|---|
| Schema/type/field design, nullability, pagination, mutations shape | `graphql-api` |
| Resolver architecture, DataLoader/N+1, authorization placement | `graphql-api` |
| Query cost controls, error modeling, operation-level testing | `graphql-api` |
| Federation concept ("what is an entity, why federate") | `graphql-api` (brief) |
| Federation 2 directive syntax and Apollo composition semantics | **this skill** |
| Apollo Server v4 subgraph runtime code | **this skill** |
| Apollo Router config/CORS/local operation | **this skill** |
| Rover CLI (`check`/`compose`/`publish`) | **this skill** |
| GraphOS/Studio graph refs, variants, contracts | **this skill** |
| CI gating specific to Apollo composition checks | **this skill** |

If you're touching both layers in one task, apply `graphql-api`'s review checklist to the schema/resolver content and this skill's checklist to the Apollo tooling around it.

## Federation 2 Directives & Entities

Federation 2 subgraphs import directives from a federation-specific link, not a bare `@key` in the global namespace:

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.3",
        import: ["@key", "@shareable", "@override", "@requires", "@provides", "@external", "@tag"])

type Product @key(fields: "id") {
  id: ID!
  name: String!
  price: Int! @shareable
  inventoryCount: Int @external
  isInStock: Boolean! @requires(fields: "inventoryCount")
}
```

Directive quick reference:

- `@key(fields: "...")` — declares the entity's primary key(s); a type can have multiple `@key`s for different lookup shapes.
- `@shareable` — allows the same field to be resolved by more than one subgraph without an ownership conflict.
- `@external` — marks a field as owned by another subgraph but referenced here (commonly alongside `@requires`/`@provides`).
- `@requires(fields: "...")` — this subgraph needs the named external field(s) resolved before it can compute its own field.
- `@provides(fields: "...")` — this subgraph can resolve a field that's normally fetched elsewhere, as an optimization.
- `@override(from: "SubgraphName")` — migrates ownership of a field from one subgraph to another; use during controlled cutovers, not as a permanent pattern.
- `@inaccessible` — hides a field/type from the public API surface of the composed graph without removing it from the subgraph schema (useful for staged rollouts).
- `@tag` — attaches metadata consumable by contracts/tooling; does not change runtime behavior.
- `@interfaceObject` — lets a subgraph contribute fields to all implementers of an interface without knowing every concrete type.
- `@composeDirective` — opts a custom directive into composition instead of being stripped.

Entity resolution lives in `__resolveReference`:

```ts
const resolvers = {
  Product: {
    __resolveReference(reference: { id: string }) {
      return productsById.get(reference.id);
    },
  },
};
```

Pitfall check: Federation 1 syntax (`@key` without the `@link` import, `extend type X @key(...)` with `@extends`) is legacy. If a subgraph schema is missing the `@link` directive to `specs.apollo.dev/federation/v2.x`, confirm with the user whether the repo is intentionally still on Federation 1 before "fixing" directive usage — don't silently upgrade the federation version as a side effect of an unrelated change.

## Apollo Server v4 Subgraphs

Federation 2 subgraphs typically use `@apollo/subgraph` + `@apollo/server` v4:

```ts
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import { typeDefs } from './schema.js';
import { resolvers } from './resolvers.js';

const server = new ApolloServer({
  schema: buildSubgraphSchema({ typeDefs, resolvers }),
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async ({ req }) => buildRequestContext(req), // auth, loaders, tenant — see graphql-api
});
```

For integration into an existing Express app (common when a subgraph shares a process with REST routes), use `expressMiddleware` instead of `startStandaloneServer` — pair with `node-backend` for the surrounding app/middleware conventions.

Version discipline (read-only discovery, not an assumption):

```bash
# Discover what's actually pinned before writing code against it — do not assume "latest v4 API"
npm pkg get dependencies.@apollo/server dependencies.@apollo/subgraph \
  devDependencies.@apollo/server devDependencies.@apollo/subgraph
npm ls @apollo/server @apollo/subgraph 2>/dev/null
```

Apollo Server v4's API differs meaningfully from v3 (no more `apollo-server`/`apollo-server-express` packages, explicit `startStandaloneServer`/`expressMiddleware`, different plugin lifecycle). If the repo is still on v3, don't silently write v4-shaped code — flag the version gap to the user.

## Apollo Router — Local Operation, Config, CORS

**Discovery first, no installs.** Check what's present before assuming a binary, config file, or version:

```bash
# Read-only discovery — do not install anything if these come back empty
command -v router >/dev/null && router --version || echo "router binary not found on PATH"
```

Use the host's repository file-search tool to locate `router.yaml` or `router.yml`; do not assume the config filename or search the whole filesystem blindly.

If the Router binary isn't present, tell the user what's missing and let them decide how to obtain it (their install method, their pinned version) — do not download or install it yourself as part of this skill.

Minimal local `router.yaml` shape, annotated for the concerns that most commonly bite:

```yaml
supergraph:
  listen: 127.0.0.1:4000
  path: /graphql

headers:
  all:
    request:
      - propagate:
          named: "Authorization"   # only propagate headers you intend clients/subgraphs to share

cors:
  origins:
    - http://localhost:3000        # explicit allow-list; avoid `allow_any_origin: true` outside a throwaway local sandbox
  allow_credentials: true
  methods: [GET, POST, OPTIONS]

include_subgraph_errors:
  all: false                        # keep off in anything resembling production; noisy in local dev is fine, opt-in
```

Running the Router locally against an already-composed supergraph (no publish, no APOLLO_KEY required in this mode):

```bash
router --config router.yaml --supergraph supergraph.graphql
```

Running in "managed federation" mode against GraphOS instead of a local file requires `APOLLO_KEY` and `APOLLO_GRAPH_REF` in the environment — see the secrets section before doing this.

## Rover CLI — Checks, Compose, Publish

Rover is the CLI for schema checks, local composition, and registry publication. Treat these as three different risk tiers:

```bash
# Discovery — always safe
rover --version                          # confirm the pinned version in use; don't assume "latest"
rover config whoami                      # confirms auth context WITHOUT printing the key itself
```

```bash
# Local, non-mutating — safe to run freely once subgraphs are reachable
rover supergraph compose --config supergraph.yaml > supergraph.graphql
```

```bash
# Registry checks — validate against GraphOS's known composition/operations without changing the published schema.
# Still requires APOLLO_KEY to authenticate; treat the key as a secret even though the check itself is read-only.
rover subgraph check <graph-ref> --name <subgraph-name> --schema ./products.graphql
```

```bash
# Registry mutation — REQUIRES explicit user authorization naming graph ref + variant before running.
# This changes what GraphOS serves as the published schema for that variant.
rover subgraph publish <graph-ref> --name <subgraph-name> --schema ./products.graphql --routing-url <url>
```

`supergraph.yaml` for local composition typically points at subgraph SDL files or running endpoints:

```yaml
federation_version: 2
subgraphs:
  products:
    routing_url: http://localhost:4001/graphql
    schema:
      subgraph_url: http://localhost:4001/graphql   # or: file: ./products.graphql
  reviews:
    routing_url: http://localhost:4002/graphql
    schema:
      file: ./reviews.graphql
```

Rule of thumb: `check` and `compose` are safe to run repeatedly during investigation; `publish` is a one-way registry mutation and belongs in the "ask first" bucket alongside anything that changes GraphOS graph configuration.

## GraphOS / Apollo Studio

Key vocabulary:

- **Graph** — a named entry in GraphOS (e.g. `my-team-graph`).
- **Variant** — an environment/branch of that graph (e.g. `current`, `staging`, `my-feature`). A **graph ref** is `graph-id@variant`.
- **Checks** — composition/operation/schema diff results Studio computes for a proposed schema, surfaced via `rover ... check` and visible in the Studio UI.
- **Contracts** — filtered views of a graph (often using `@tag`/`@inaccessible`) published to specific consumers.

Read-only, safe to do anytime: viewing check results, operation metrics, schema history, and field usage in Studio; running `rover ... check` against an existing graph ref the user has already granted access to.

Requires explicit user authorization before doing: creating/deleting graphs or variants, publishing a subgraph or supergraph schema, creating or rotating an `APOLLO_KEY`, editing contracts, or changing router-managed-federation settings. If a task seems to call for one of these, state the exact action and graph ref/variant and get an explicit go-ahead before running it — don't infer authorization from "the user asked me to fix the schema."

## Testing the Composed Graph via Router

Per `graphql-api`'s federation guidance, the Router-facing composed graph is the real client contract — subgraph-only tests are necessary but not sufficient. Concrete local sequence:

```bash
# 1. Start each subgraph locally (however the repo normally starts them, e.g. npm run dev per subgraph)

# 2. Compose locally — no registry mutation
rover supergraph compose --config supergraph.yaml > supergraph.graphql

# 3. Start the Router against the local composed schema — no APOLLO_KEY needed in this mode
router --config router.yaml --supergraph supergraph.graphql

# 4. Exercise real operations against the Router endpoint, not individual subgraphs
curl -s http://localhost:4000/graphql \
  -H 'content-type: application/json' \
  -d '{"query":"query { product(id: \"1\") { id name isInStock } }"}'
```

For UI-driven flows that ultimately call the Router, pair with `playwright-testing` to assert against the Router endpoint (or a UI that calls it) rather than mocking it away — a passing subgraph unit test suite can still hide a broken cross-subgraph entity reference that only appears once composed.

## CI Checks

Recommended shape for a federation-aware CI pipeline:

1. **Pin the Rover (and Router, if used in CI) version explicitly** — use an organization-approved fixed container/image digest, lockfile-recorded version, or checksum-verified artifact. Do not add an unreviewed `curl | sh` bootstrap step, and never let CI silently float to "latest."
2. **Composition/check job (PR gate, non-mutating):** run `rover subgraph check` (or `rover supergraph compose` for a purely local check with no registry account at all) and fail the build on composition errors or breaking-change violations.
3. **Operation validation job:** stand up subgraphs + Router in CI (or a docker-compose equivalent) and run the same representative operations described above against the composed endpoint.
4. **Publish job — separate from the PR gate.** Only runs post-merge on the target branch, reads `APOLLO_KEY`/`APOLLO_GRAPH_REF` from CI's secret store (never from a committed file), and ideally requires a manual approval gate for anything beyond a routine variant.
5. **Never echo secret values in CI logs** — see below.

## Secret-Safe Handling of `APOLLO_KEY` / `APOLLO_GRAPH_REF`

- Never print, log, `echo`, or include the literal value of `APOLLO_KEY` in command output, commit messages, PR descriptions, or chat responses — including partial/truncated forms.
- Check presence without exposing value:

  ```bash
  [ -n "$APOLLO_KEY" ] && echo "APOLLO_KEY is set" || echo "APOLLO_KEY is not set"
  ```

- Store GraphOS keys for publish/deploy workflows only in CI secret storage or an organization-approved secret manager. Do not ask an agent to source a key from a local shell profile or `.env` file. If an organization permits a developer credential for a read-only local check, the user must supply and authorize that environment outside the agent; never read or print its value. Never write a key into a tracked file.
- `APOLLO_GRAPH_REF` (`graph-id@variant`) is not itself a credential, but it identifies exactly which graph/variant a command will affect — always state it explicitly when proposing a `publish`/`check` command so the user can confirm it's the intended target, and still avoid gratuitously pasting it into logs alongside key-adjacent output.
- Before any command that reads these variables, confirm with the user (if not already explicit in the task) which graph ref/variant is intended — a wrong `APOLLO_GRAPH_REF` on a `publish` call overwrites the wrong variant.
- If asked to run `rover subgraph publish` or any GraphOS configuration change, restate the exact graph ref, variant, and effect, and get explicit confirmation before executing — this is a remote mutation, not a read.

## Ownership & Re-review

- **Owner:** Hermes skills corpus maintainers.
- **Approval constraint:** This skill is approved for Apollo Federation 2, Apollo Server v4 subgraphs, Apollo Router, Rover, and GraphOS/Studio workflows only. It does not establish guidance for unrelated Apollo products or non-Apollo GraphQL runtimes.
- **Re-review trigger:** Re-review before adopting an Apollo Federation major version, a materially changed Router configuration schema, a Rover CLI breaking change, new linked scripts/templates, or a broader credential/permission scope.
- **Review evidence:** Verify every cited Rover command against the pinned CLI version or current official Apollo documentation before treating it as executable guidance. Re-run the secret-safety review whenever credential handling changes.

## Vendor-Runtime Roadmap

Apollo (Server + Router + Rover + GraphOS) is **one** vendor-specific way to run a federated/composed GraphQL graph. It is not the only one:

- **GraphQL Yoga** (with the **Envelop** plugin chain) is a different vendor runtime with its own execution/plugin model, its own federation-gateway packages, and Envelop-specific plugin composition semantics that don't map 1:1 onto Apollo's directive/Router/Rover model.

This skill intentionally does **not** cover Yoga/Envelop internals. Vendor-neutral GraphQL concepts still route through `graphql-api` regardless of runtime. A dedicated `graphql-yoga` (or similarly named) skill should be created **only when real adoption requires genuinely Yoga/Envelop-specific behavior** — e.g. a repo is actually running Yoga in production and needs guidance on Envelop plugin ordering, Yoga's federation gateway setup, or Yoga-specific request lifecycle hooks. Don't create that skill preemptively or speculatively; until there's a real Yoga codebase to support, treat Yoga questions as out of scope here and note the gap rather than forcing Apollo-shaped answers onto a different runtime.

## Common Pitfalls

1. **Assuming Rover/Router are installed and at "latest."** Always discover the actual installed version first (`rover --version`, `router --version`); never assume, and never install/upgrade without the user asking.
2. **Writing Federation 1-style directives** (`@extends`, bare `@key` with no `@link` import) into a Federation 2 codebase, or vice versa, without checking which spec version the `@link` directive declares.
3. **Publishing before composing/checking locally.** `rover subgraph publish` should follow a green `rover subgraph check` / local `rover supergraph compose`, not precede it.
4. **Testing only against subgraph endpoints.** A subgraph can pass its own tests while the composed graph fails to resolve a cross-subgraph entity reference — always exercise the Router.
5. **Forgetting Router CORS config** — a Router that works via `curl` but is unreachable from a browser client usually means `cors.origins` doesn't include the client's origin.
6. **Treating `APOLLO_GRAPH_REF` as harmless boilerplate copy-pasted from an example.** Wrong variant on a `publish` overwrites the wrong environment's schema.
7. **Printing verbose Rover/Router debug output that echoes Authorization headers or key material.** Redact before sharing logs.
8. **Skipping CI composition checks and relying on manual `rover` runs.** Composition/check should be a required, automated PR gate, not a developer habit.
9. **Conflating `check` (safe, read-only) with `publish` (mutating).** Both need `APOLLO_KEY`, but only one changes what's served — don't let "it needs a key anyway" blur the authorization line.
10. **Reaching for Yoga/Envelop-specific guidance from this skill.** This skill is Apollo-specific; see the Vendor-Runtime Roadmap section instead of stretching Apollo patterns onto a different runtime.

## Verification Checklist

- [ ] Confirmed via read-only commands what Rover/Router versions (if any) are actually installed, before writing any commands against them.
- [ ] Federation directives match the spec version declared in the subgraph's `@link` directive (Federation 2 vs legacy Federation 1 syntax not mixed).
- [ ] Subgraph schema composes locally (`rover supergraph compose` or equivalent) before any check/publish against GraphOS.
- [ ] Router config reviewed for CORS origins and header propagation before running locally.
- [ ] Composed graph tested through the Router endpoint with real operations, not only against individual subgraphs.
- [ ] CI pipeline pins Rover/Router versions explicitly and runs composition checks as a required PR gate, with `publish` isolated to a separate, later, secret-scoped job.
- [ ] No `APOLLO_KEY` value ever printed, logged, or pasted into output; presence checked without echoing the value.
- [ ] `APOLLO_GRAPH_REF` (and any other GraphOS variant target) explicitly confirmed with the user before any command that reads it.
- [ ] Any `rover ... publish` or GraphOS graph/variant/contract configuration change had explicit, specific user authorization before execution — not inferred from a general task description.
- [ ] Vendor-neutral schema/resolver/authorization/testing concerns were deferred to `graphql-api` rather than re-derived here.
- [ ] Yoga/Envelop-specific questions were flagged as out of scope rather than answered with Apollo-shaped assumptions.
