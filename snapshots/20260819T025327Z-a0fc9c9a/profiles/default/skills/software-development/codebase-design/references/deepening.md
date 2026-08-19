# Deepening Modules

Use this reference after identifying a **cluster** that may become a deeper **module**. It assumes the vocabulary in the parent skill: **module**, **interface**, **seam**, **port**, and **adapter**.

## Dependency Categories

Classify each material dependency before placing a seam. The category determines how the deepened module is tested through its external interface.

### 1. In-process

Pure computation or in-memory state with no I/O.

- Merge the cluster when it has one coherent responsibility.
- Test directly through the new module interface.
- Do not introduce an adapter merely to make a pure function look abstract.

### 2. Local-substitutable

A dependency with a local test stand-in that preserves the semantics relevant to the module: for example, an in-memory filesystem or a realistic local database runtime.

- Deepen the module if the stand-in is sufficient for the behaviours under test.
- Run interface-level tests against the stand-in.
- Keep the substitution seam internal unless callers genuinely need to choose the dependency.
- Validate semantic gaps: a stand-in may differ from production in extensions, transactions, locking, consistency, query behaviour, or failure modes.

If no credible stand-in exists, treat the dependency as remote-but-owned until one exists. Do not hide the category by class-level mocking.

### 3. Remote but Owned: Ports and Adapters

A networked dependency you own: another internal service, a microservice, or an organisation-controlled API.

- Define a **port** at the seam around the deep module’s intention, not an endpoint-for-endpoint transport wrapper.
- Inject a production adapter such as an HTTP adapter, gRPC adapter, or queue-consumer adapter.
- Use an in-memory adapter in fast interface-level tests.
- Add contract or integration coverage where the wire contract is material.

Recommendation shape:

> Define a port at the seam, implement a production transport adapter and an in-memory adapter for tests, so the logic stays in one deep module even though its dependency is deployed elsewhere.

### 4. True External

A third-party provider you do not control: a payment provider, messaging API, SaaS platform, or vendor SDK.

- Inject the provider through a port around your module’s intention.
- Use a mock or in-memory adapter for fast deterministic interface-level tests.
- For durable integrations, supplement mocks with a contract test, sandbox run, emulator, or recorded-response suite to detect provider drift.
- Make idempotency, retry, timeout, and error classification observable at the deep module interface when callers must act on them.

## Seam Discipline

- **One adapter requires a reason; multiple adapters are strong evidence.** Production plus test adapters commonly justify a port, but a volatile vendor dependency, anti-corruption layer, or imminent replacement can justify one earlier.
- **Do not mirror a provider.** A port should model the deep module’s needs, not reproduce every method of an SDK, database client, or remote API.
- **Internal and external seams differ.** A deep module may use private internal seams for its own implementation tests. Do not expose them through the external interface simply because tests use them.
- **Place the seam where policy changes.** Put invariants, validation, orchestration, retries, and provider selection behind the deep module where they vary together.

## Testing Strategy: Replace, Don’t Layer

1. Write tests at the deep module’s external interface.
2. Assert observable outcomes, documented errors, and essential compatibility guarantees—not internal state or collaborator call sequences.
3. Migrate or retain tests that preserve distinct behaviours not yet covered through the new interface.
4. Delete former shallow-module tests only after interface-level coverage is equivalent or stronger and any compliance obligations are met.
5. During phased migration, temporary overlap is acceptable; give former structural tests an explicit removal condition rather than keeping them indefinitely.

If a test fails after an internal refactor without a documented behavioural change, it was likely testing past the interface. If documented behaviour changes, update the interface contract and its tests deliberately.

## Deepening Candidate Signals

Prioritize a cluster when several signals coincide:

- callers duplicate the same policy or coordinate the same state transition;
- a shared parameter bundle or setup ritual appears in multiple callers;
- changes fan out across the cluster and its callers;
- tests need extensive internal setup or assertions;
- the cluster has one responsibility that can be stated in one sentence;
- deletion would force meaningful rules to reappear across callers.

Do not deepen merely because code is adjacent. Avoid a merger when modules change independently, serve distinct responsibilities, or the proposed module becomes a broad “utility” with unrelated operations.
