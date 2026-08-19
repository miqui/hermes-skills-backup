---
name: spring-boot-engineer
description: Use when building, reviewing, or evolving Spring Boot services, REST APIs, reactive endpoints, data access layers, security, and cloud-native service integrations. Covers practical defaults for modern Spring Boot applications with strong testing, observability, and maintainable architecture.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [spring-boot, java, spring-security, spring-data, webflux, microservices]
    related_skills: [java-coding-standards, api-governance, systematic-debugging, code-performance-engineering]
---

# Spring Boot Engineer

## Overview

Use this skill for practical Spring Boot service work: new APIs, incremental feature work, data access layers, security setup, testing, production-hardening, and service-to-service integration. It is intended for real application engineering, not just framework boilerplate.

This skill assumes modern Spring Boot 3.x and Spring Framework 6+ conventions. It prefers current LTS-era Java features and modern Spring patterns when the project baseline allows, while still respecting the actual target runtime of the repository. The goal is to produce services that are easy to reason about, test, secure, and operate.

For low-level Java style decisions, pair with `java-coding-standards`. For API contract quality and governance, pair with `api-governance`. For incident-driven debugging or failing builds/tests, pair with `systematic-debugging`. For endpoint latency, throughput, JVM/runtime behavior, data-access hot paths, N+1 queries, WebFlux/blocking trade-offs, or performance-sensitive code review, pair with `code-performance-engineering`.

## When to Use

Use this skill when:
- Building REST APIs with Spring Boot
- Adding controllers, services, repositories, DTOs, and configuration
- Implementing authentication or authorization with Spring Security 6+
- Designing or reviewing Spring Data JPA persistence layers
- Building reactive endpoints with WebFlux where non-blocking I/O is appropriate
- Integrating Actuator, Micrometer, health checks, or cloud-native concerns
- Writing or improving Spring Boot tests using test slices, MockMvc, or Testcontainers
- Modernizing older Spring code toward current Boot 3.x conventions

Do not use this skill when:
- The task is pure framework setup with no application-specific design decisions
- The problem is primarily generic Java style rather than Spring-specific engineering
- The service is not Spring-based and another platform skill is a better fit
- The user needs only a narrow one-off fix with no architectural or framework implications

## Technology Baseline

### Spring baseline
- Prefer Spring Boot 3.x conventions
- Prefer Spring Security 6+ style configuration (`SecurityFilterChain`, method security, explicit beans)
- Prefer Jakarta namespace APIs used by modern Spring Boot releases
- Prefer `WebClient` over legacy `RestTemplate` for new HTTP client work unless the project standard says otherwise

### Java baseline
- Prefer the **latest LTS** or the project's approved modern baseline rather than anchoring guidance to Java 17 by default
- Use modern Java features when they improve clarity and match the target runtime: records, sealed types, switch expressions, pattern matching, text blocks, virtual threads where appropriate
- If the repo is pinned to an older runtime, follow the repo baseline explicitly instead of forcing newer syntax

### Default architectural bias
- Clear layered structure: controller → service → repository/integration
- Constructor injection over field injection
- DTOs at boundaries, domain objects kept intentional
- Explicit validation and error mapping
- Strong tests around behavior, not just bean wiring
- Observability and operational clarity included from the start

## Core Workflow

### 1. Understand the service boundary
Before writing code, determine:
- what the service owns
- what the API contract should expose
- what data model or aggregate is involved
- what security and authorization rules apply
- whether the workload is blocking, non-blocking, batch, or event-driven

A surprising amount of Spring complexity comes from skipping this step and letting repository shape drive the service design.

### 2. Choose the right execution model
Use the simplest model that fits the workload.

Prefer classic MVC + blocking persistence when:
- the application is CRUD-heavy
- the persistence layer is JPA/Hibernate
- the workload is request/response with bounded concurrency
- team familiarity and operational simplicity matter more than theoretical throughput

Prefer WebFlux/reactive only when:
- the workload is genuinely I/O-heavy and benefits from non-blocking flows
- downstream dependencies are also reactive or non-blocking
- the team understands reactive debugging and testing costs
- reactive end-to-end behavior is intentional, not cosmetic

Do not mix blocking JPA flows into a reactive design casually. If a stack is reactive in name only but blocks everywhere, it becomes harder to debug without providing the intended benefit.

### 3. Build the application layers deliberately
A healthy Spring Boot feature usually includes:
- request/response DTOs
- controller methods with validation
- service-layer business logic
- repository or client integration
- domain-specific exceptions and error handling
- tests at the appropriate level

Keep controllers thin. Put orchestration and business decisions in services. Keep repositories focused on persistence/query concerns rather than business workflows.

### 4. Add security and configuration early
Do not bolt security on at the end.

Establish early:
- authentication mechanism
- authorization rules
- configuration properties shape
- secrets and credential sourcing
- actuator exposure policy
- CORS and CSRF posture where relevant

Spring applications often become brittle when security and configuration are treated as afterthoughts.

### 5. Make it testable and operable
A feature is not complete when it compiles. It should also be:
- verifiable in unit and slice tests
- observable with logs/metrics/health signals
- configurable without code edits
- understandable to another engineer scanning the package structure

## Service Design Guidelines

### Package and class structure
A common baseline layout:

```text
src/main/java/com/example/app/
  config/
  controller/
  service/
  repository/
  domain/
  dto/
  integration/
  security/
```

Adjust structure to the codebase, but keep responsibilities obvious. Avoid dumping everything into `service` and `util` packages.

### API layer
- Use `@RestController` for HTTP APIs
- Validate incoming payloads with Bean Validation annotations and `@Valid`
- Return DTOs, not JPA entities
- Use consistent status codes and exception mapping
- Keep pagination, filtering, and idempotency behavior explicit

### Service layer
- Put business rules and orchestration here
- Keep transaction boundaries intentional
- Prefer explicit method names that reflect domain behavior, not just CRUD verbs
- Make side effects and integration calls visible in the method flow

### Data layer
- Use Spring Data repositories where they simplify the code
- Use projections/specifications/query methods intentionally, not mechanically
- Keep entity relationships understandable and fetch behavior deliberate
- Be conservative with cascade behavior and bidirectional relationships

### Configuration
- Prefer `@ConfigurationProperties` for structured config over large piles of `@Value`
- Separate application config from secret material
- Keep environment-specific behavior visible in configuration, not hidden in `if` statements scattered through code

## Security Defaults

- Use `SecurityFilterChain` and explicit authorization rules
- Avoid field injection and magical global state in security code
- Do not expose raw internal exceptions to clients
- Keep JWT/OAuth2 decisions aligned with the actual deployment and trust model
- Store secrets outside source-controlled `application.properties` or `.yml`
- Review Actuator endpoint exposure carefully in non-local environments

When the task is security-heavy, load `references/security.md` and align the implementation with the actual auth model rather than copy-pasting a generic JWT setup.

When the task involves OAuth2 social login, Spring Authorization Server, session-based auth, SAML2 SSO, security testing, or multi-tenant security, load `references/security-advanced.md`.

## Data Access Defaults

- Prefer explicit transaction boundaries
- Default read paths to `@Transactional(readOnly = true)` where appropriate
- Use optimistic locking/versioning when concurrent updates matter
- Avoid N+1 query traps and over-eager entity graphs
- Use DTO projections or query tuning when read paths are performance-sensitive
- Model entities for correctness first, then optimize hot paths intentionally

When the task is persistence-heavy, load `references/data.md`.

When the task involves NoSQL (MongoDB/Redis), Spring Cache abstraction, Caffeine, or RFC 9457 Problem Details, load `references/advanced-data.md`.

## Web and API Defaults

- Prefer request/response DTOs as records when the project baseline allows
- Use global exception handling for consistent API errors
- Keep controllers thin and validation close to the edge
- Generate location headers on creates when appropriate
- Keep endpoint naming and resource structure consistent

When the task is endpoint-heavy, load `references/web.md`.

## Cloud-Native and Integration Defaults

- Add health/readiness/liveness behavior intentionally
- Use Micrometer/Actuator rather than ad hoc operational hacks
- Use resilient client behavior for external dependencies where justified
- Treat service discovery, config servers, gateways, and circuit breakers as architecture choices, not automatic defaults
- Keep deployment/runtime concerns compatible with the actual platform rather than aspirational architecture diagrams

When the task is integration or microservice-platform heavy, load `references/cloud.md`.

When the task involves Micrometer metrics, OTLP/Prometheus export, distributed tracing, structured logging, custom health indicators, or audit events, load `references/observability.md`.

When the task involves GraalVM native image compilation, AOT processing, runtime hints, or native deployment, load `references/native-image.md`.

When the task involves structuring a modular monolith, verifying module boundaries, externalizing module events, or testing modules in isolation with Spring Modulith, load `references/modulith.md`.

## Testing Expectations

A solid Spring Boot change usually includes the right mix of:
- unit tests for business rules
- slice tests for controllers/repositories/security where useful
- integration tests for key flows
- Testcontainers for real dependency behavior when the boundary matters

Use the narrowest useful test first. `@SpringBootTest` is powerful, but it is not the default answer for every class.

When the task is test-heavy, load `references/testing.md`.

## Output Expectations

For substantive Spring Boot implementation work, aim to provide or update:
1. DTOs or boundary models
2. controller endpoints
3. service-layer behavior
4. persistence or client integration
5. configuration updates if needed
6. security rules if the endpoint requires them
7. tests matching the risk and scope of the change
8. a short explanation of the main design choices

Not every task needs all eight, but the response should make the architectural shape clear.

## Common Pitfalls

1. **Defaulting to Java 17-era advice even when the project can use newer LTS features.**
   Prefer the latest LTS or the repo's approved modern baseline unless the repository is explicitly pinned lower.

2. **Using WebFlux because it sounds modern.**
   Reactive complexity is only worth it when the workload and dependency graph actually benefit.

3. **Returning entities directly from controllers.**
   This couples persistence shape to API shape and makes evolution harder.

4. **Letting repositories absorb business logic.**
   Spring Data is convenient, but business decisions belong in the service layer.

5. **Overusing `@SpringBootTest`.**
   Full-context tests are valuable, but many failures are better caught with faster slice or unit tests.

6. **Treating security as an afterthought.**
   Authorization rules, config handling, and secret sourcing should be part of the design, not post-processing.

7. **Mixing blocking and reactive code blindly.**
   If the stack blocks in critical paths, admit it and design for that reality instead of pretending it is reactive.

8. **Hiding operational concerns.**
   Logging, metrics, health behavior, and configuration clarity are part of production-ready Spring work.

9. **Using high-cardinality metric tags.**
   Tagging by `userId`, raw URI, or `requestId` creates unbounded label combinations. Use bounded tags (HTTP method, status code, route template).

10. **Mixing `@Transactional` with MongoDB.**
    MongoDB is not an XA resource. A `@Transactional` method spanning JPA + MongoDB will not roll back the MongoDB write if the JPA insert fails.

11. **Not using `ProblemDetail` on Spring 6+.**
    Custom `ErrorResponse` records duplicate the RFC 9457 structure that Spring now provides natively.

12. **Cache without TTL or stampede protection.**
    A cache without an expiry policy serves stale data indefinitely. A hot key expiry without `sync=true` triggers cache stampede.

13. **Using CGLIB proxies in a native image.**
    GraalVM Native Image cannot generate CGLIB proxies at runtime. Use `@Configuration(proxyBeanMethods = false)` and register explicit reflection hints.

14. **OAuth2 client secrets in config files.**
    Never commit `client-secret` values to source control. Use environment variables or a secrets manager.

15. **Circular module dependencies in Spring Modulith.**
    If module A depends on B and B depends on A, the verification test fails. Refactor to use events or extract shared types.

16. **Direct database access across Modulith modules.**
    Modules should not share JPA entities or repositories. Use the module's named interface or events for cross-module data access.

## Verification Checklist

- [ ] The service boundary and responsibility are clear
- [ ] The chosen execution model (MVC vs reactive) matches the real workload
- [ ] Controllers, services, and persistence/integration concerns are separated cleanly
- [ ] Validation and error handling are explicit at the API boundary
- [ ] Security and configuration choices match the deployment model
- [ ] Data access patterns and transaction boundaries are intentional
- [ ] Tests match the scope and risk of the change
- [ ] Observability and operational concerns are addressed where relevant
- [ ] If deeper topic guidance is needed, the right reference file is loaded (`web.md`, `data.md`, `advanced-data.md`, `security.md`, `security-advanced.md`, `cloud.md`, `observability.md`, `native-image.md`, `modulith.md`, `testing.md`)
