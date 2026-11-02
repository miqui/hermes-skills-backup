---
name: codebase-design
description: "Use when designing or restructuring codebase modules: deciding a module’s interface and seam, deepening shallow caller clusters, choosing dependency adapters, and defining refactor-resilient interface-level tests."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [architecture, codebase-design, modules, interfaces, seams, adapters, refactoring, testability]
    related_skills: [idea-refine, writing-plans, test-driven-development, simplify-code, subagent-driven-development, requesting-code-review]
---

# Codebase Design

## Overview

Design **deep modules**: substantial behaviour behind a small, clear **interface**, placed at an intentional **seam**, and testable through that interface. The aim is **leverage** for callers, **locality** for maintainers, and tests that survive internal refactors.

This skill is about the shape of modules inside a codebase. It does not replace protocol-specific API design skills, product ideation, implementation planning, or the RED-GREEN-REFACTOR discipline. Use it to make those downstream activities simpler by deciding what callers should need to know—and what the module should hide.

## When to Use

Use this skill when the user asks to:

- Design or simplify a module’s **interface**.
- Decide where a **seam** belongs during a refactor.
- Deepen a cluster of shallow, highly coupled modules.
- Reduce parameter sprawl, pass-through wrappers, duplicated policy, or caller knowledge.
- Make a module testable through observable outcomes rather than internal state.
- Decide whether an injected dependency needs a real **port** and multiple **adapters**.
- Compare radically different interface designs before committing to a substantial refactor.

Typical requests include:

- “These classes feel shallow; how should we deepen them?”
- “Where should the seam go around this persistence and business logic?”
- “Design a smaller interface for this order-processing module.”
- “Show me several interface designs and recommend the strongest.”
- “Our tests know too much about internals—reshape this module.”

Do not use this skill for:

- Product or feature direction before a codebase candidate exists; use `idea-refine`.
- HTTP, GraphQL, gRPC, event, or OpenAPI contract mechanics; use the relevant API-design skill.
- Turning an approved design into granular implementation tasks; use `writing-plans`.
- A narrow post-change cleanup or review pass; use `simplify-code`.
- Strict test-first execution; use `test-driven-development`.

## Glossary

Use these terms consistently. The vocabulary is deliberately scale-agnostic.

**Module** — anything with an **interface** and an **implementation**: a function, class, package, or tier-spanning slice. Avoid: unit, component, service.

**Interface** — everything a caller must know to use a module correctly: types, invariants, ordering constraints, error modes, required configuration, and performance characteristics. It is broader than a type signature or a language-level `interface` declaration. Avoid using “API” when the concern is an internal module interface.

**Implementation** — the code inside a module that realizes its behaviour. Say **adapter** when the seam role is the topic: a Postgres repository and an in-memory fake can both be adapters at the same seam. Say implementation when the code inside is the topic.

**Depth** — leverage at the interface: how much useful behaviour a caller or test can exercise per unit of interface it must learn. A module is **deep** when it hides substantial complexity behind a small interface; it is **shallow** when its interface nearly exposes or mirrors its implementation.

**Seam** — a location where behaviour can be altered without editing the caller. Extended from Michael Feathers: seam placement is a first-class design decision, not merely something to discover in legacy code. Avoid: boundary, which is overloaded with DDD’s bounded-context meaning.

**Port** — an interface defined at a seam to abstract a cross-seam dependency; it is the slot an **adapter** fills. Use port when the injection-point role matters, especially for remote-but-owned and true-external dependencies.

**Adapter** — a concrete thing that satisfies a port at a seam. It describes a role, not the size or complexity of its code.

**Cluster** — a group of shallow modules with one coherent responsibility, identified by shared data, shared invariants, duplicated policy, or high coupling. Deepening replaces the cluster with one deeper module.

**Leverage** — what callers receive from depth: more capability per unit of interface learned. One implementation pays back across many call sites and tests.

**Locality** — what maintainers receive from depth: changes, bugs, knowledge, and verification concentrate in one place instead of spreading across callers.

**AI-navigable** — a module whose small, explicit interface and documented behavioural contract allow a human or AI agent to reason about callers without reading implementation details.

## Deep vs. Shallow

A deep module has a small interface and hides meaningful behaviour:

```text
┌─────────────────────┐
│   Small Interface   │  Few operations; simple caller obligations
├─────────────────────┤
│                     │
│  Deep Implementation│  Policy, coordination, edge cases, I/O details
│                     │
└─────────────────────┘
```

A shallow module has an interface that mostly reproduces its implementation or forces callers to coordinate its policy:

```text
┌─────────────────────────────────┐
│       Large Interface           │  Many operations; complex setup/ordering
├─────────────────────────────────┤
│  Thin Implementation            │  Mostly forwards or exposes mechanics
└─────────────────────────────────┘
```

When evaluating an interface, ask:

- Can callers achieve their goal through fewer operations?
- Can parameters become an intention-revealing request or result rather than a bag of mechanics?
- Can invariants, retries, ordering, validation, and provider details move inside the module?
- If the module disappeared, would its complexity reappear across its callers? If yes, it is earning its keep.

## Core Principles

1. **Depth is a property of the interface, not implementation size.**
   Retain the idea of depth-as-leverage; reject lines-of-code ratios as a measurement because they reward padding rather than value.

2. **Use the deletion test.**
   Imagine removing the module. If complexity vanishes, it was a pass-through. If its rules and coordination reappear in many callers, it was providing leverage and locality.

3. **The interface is the test surface.**
   Tests should cross the same seam as callers and assert observable outcomes. A test that fails on a refactor without a documented behavioural change is probably testing past the interface.

4. **A module may have internal seams.**
   Internal seams may aid implementation tests or isolate volatile dependencies, but they do not automatically belong in the external interface.

5. **Justify a seam by real variation.**
   One adapter requires explicit justification; production and test adapters are strong evidence that a seam is real. An unstable vendor dependency, a deliberate anti-corruption layer, or an imminent replacement can also justify one before a second production adapter exists.

## Assessment Workflow

### 1. Inspect the caller cluster

Map the candidate and its callers before proposing abstractions. Look for:

- duplicated validation, retry, ordering, or error policy;
- repeated parameter bundles and mechanical setup;
- pass-through wrappers;
- callers coordinating state transitions that should be local;
- tests that must create or inspect internal objects to verify useful behaviour;
- frequent changes that fan out across multiple callers.

State the candidate’s responsibility in one sentence. If it cannot be stated coherently, do not deepen yet: the cluster may contain more than one responsibility.

### 2. Describe the current interface as callers experience it

Capture more than method names. Document:

- operations and parameters;
- caller-owned invariants and ordering;
- error modes and recovery responsibilities;
- required configuration and performance assumptions;
- dependencies that callers must understand;
- the observable outcomes callers and tests actually need.

### 3. Choose whether the candidate earns a deeper module

Prioritize candidates with high caller count, concentrated policy duplication, costly test setup, frequent coordinated changes, or a clear shared responsibility. Avoid deepening when modules vary independently, the apparent duplication is accidental, or a single simple function is already the clearest interface.

### 4. Classify dependencies

Read `references/deepening.md` and classify every material dependency:

- in-process;
- local-substitutable;
- remote but owned;
- true external.

The classification determines whether a seam belongs externally, internally, or not at all, and how interface-level tests should exercise it.

### 5. Design the external seam

Propose the smallest interface that lets callers state an intention and receive an observable outcome. Put implementation mechanisms behind it. Specify:

- operations, parameters, and results;
- invariants and ordering rules;
- error modes;
- required configuration and performance characteristics;
- what behaviour, policy, and dependencies are hidden;
- which ports and adapters are justified.

### 6. Replace, don’t layer, the tests

Write or migrate tests at the new interface. Preserve externally observable behaviours, compatibility guarantees, and important failures. Replace tests that only pin former internal structure after the interface-level tests provide equivalent or better coverage. See `references/deepening.md`.

### 7. Explore alternatives when design ambiguity is real

When several viable seam placements or interfaces remain, read `references/design-it-twice.md`. It uses parallel designs—not a vote—to expose trade-offs in depth, locality, and seam placement.

### 8. Hand off the approved design

Once the module interface and seam are chosen, use `writing-plans` to make implementation tasks and `test-driven-development` to execute behaviour changes safely.

## Designing for Testability

Examples use TypeScript, but the principles apply in every language.

### Accept dependencies; do not construct volatile dependencies in callers

```typescript
// The module receives its dependency at an internal seam.
function processOrder(order: Order, payments: PaymentsPort): ProcessResult {}

// Callers do not need to know which provider is constructed.
function processOrder(order: Order): ProcessResult {
  const payments = new StripePayments();
}
```

A port is justified when the dependency truly varies: for example, a production provider adapter and an in-memory or mock adapter for tests.

### Prefer explicit results and observable outcomes

```typescript
// A caller can observe the outcome directly.
function calculateDiscount(cart: Cart): Discount {}

// When a side effect is the module’s job, expose the intention and result,
// not provider mechanics.
function submitPayment(request: PaymentRequest): PaymentResult {}
```

Side effects such as persistence, messages, and payments are often unavoidable. Keep transport and provider mechanics behind the seam; make outcomes, error modes, and idempotency observable at the interface.

### Keep the surface small

Fewer entry points and simpler caller obligations reduce test setup and improve leverage. Do not obtain smallness by hiding necessary error, ordering, configuration, or performance facts; those are part of the interface whether or not types express them.

## Relationships

- A **module** has one external **interface** presented to callers and tests, and an **implementation** hidden behind it.
- **Depth** is a property of a module measured against its interface.
- A **seam** is where a module interface or internal port lives.
- A **port** is an interface at a cross-seam dependency; an **adapter** satisfies it.
- **Depth** creates **leverage** for callers and **locality** for maintainers.

## Common Pitfalls

1. **Calling every injected dependency a seam.** A constructor parameter alone is not proof of meaningful variation. State why the seam exists and which adapters justify it.
2. **Creating a port that mirrors every provider operation.** Put your module’s intentions at the seam, not an exhaustive wrapper around an SDK or remote API.
3. **Making the interface tiny by concealing essential facts.** Required configuration, ordering, error modes, and performance characteristics remain caller obligations even when omitted from a type signature.
4. **Exposing internal seams so tests can reach inside.** If callers do not need the seam, tests usually should not cross it either.
5. **Treating all old tests as disposable.** Preserve observable behaviours before deleting tests that pinned shallow structure.
6. **Combining every alternative into a hybrid.** A hybrid that grows the interface is a shallow module in disguise.
7. **Using mock adapters as proof of real-world integration.** Long-lived external integrations need contract, sandbox, emulator, or recorded-response verification in addition to fast mocks.
8. **Expanding scope from module design into product, API-contract, or delivery governance.** Hand off to the specialized skill once the design question changes layers.

## Verification Checklist

- [ ] The candidate has one coherent responsibility and a clearly identified caller cluster.
- [ ] The current caller obligations, including non-type-level interface facts, are explicit.
- [ ] The new interface lets callers express intentions rather than coordinate mechanics.
- [ ] The design identifies what behaviour moves behind the seam.
- [ ] Every dependency has a justified category and adapter strategy.
- [ ] Any port has an explicit rationale; it is not just an SDK-shaped wrapper.
- [ ] Tests assert documented observable outcomes through the external interface.
- [ ] Replacement or deletion of old shallow tests preserves meaningful behaviour coverage.
- [ ] If several designs were plausible, they were compared on depth, locality, seam placement, and migration cost.
- [ ] The approved design can be handed to `writing-plans` without reopening core interface decisions.

## Related Skills

- `idea-refine` — decide the product or feature direction before choosing codebase shape.
- `writing-plans` — turn the chosen module design into file-level implementation tasks.
- `test-driven-development` — evolve the approved behaviour with verified RED-GREEN-REFACTOR cycles.
- `simplify-code` — find cleanup opportunities in recent diffs; use this skill when findings expose a deeper design issue.
- `subagent-driven-development` — implement an approved plan with focused workers and review gates.
- `requesting-code-review` — review the resulting changes before publication.
