---
name: event-driven-api-design
description: "Use when designing, reviewing, governing, or implementing event-driven APIs and asynchronous contracts, including AsyncAPI, CloudEvents, Kafka-style streams, pub/sub topics, message queues, webhooks, and AWS EventBridge/SNS/SQS/Kinesis patterns. Covers event modeling, producer/consumer contracts, schema evolution, idempotency, ordering, replay, DLQs, observability, contract testing, and publication governance."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [api, event-driven, asyncapi, cloudevents, messaging, streaming, contracts]
    related_skills: [api-governance, openapi-api-designer, openapi-specification, graphql-api, grpc-api, aws-serverless, aws-messaging-and-streaming, node-backend, spring-boot-engineer, writing-plans, test-driven-development]
---

# Event-Driven API Design

## Overview

Use this skill for API projects where the main interface is not only synchronous HTTP, but an asynchronous event, message, stream, webhook, or topic/channel contract. The goal is to make event-driven APIs as reviewable, governable, testable, and consumer-friendly as REST/OpenAPI APIs.

Event-driven API work usually has two simultaneous concerns:

1. **Interaction design** — what domain events, commands, streams, topics, channels, and consumers should exist.
2. **Contract design** — how those interactions are described, validated, versioned, published, tested, and operated.

Prefer contract-first design. Use **AsyncAPI** when documenting asynchronous channels and message contracts. Use **CloudEvents** when a portable event envelope is useful across brokers, HTTP, functions, SaaS integrations, or cloud providers. Pair this skill with platform-specific skills for implementation details, especially `aws-serverless` and `aws-messaging-and-streaming` for AWS.

This skill fills the gap between general API governance and provider-specific messaging implementation. It should be loaded before jumping into broker configuration, infrastructure code, or handler implementation when the event contract itself is still being shaped.

## When to Use

Use this skill when the task involves:

- Designing an event-driven API, event catalog, message contract, webhook contract, or stream interface
- Creating or reviewing AsyncAPI documents
- Choosing between commands, events, request/reply messages, notifications, webhooks, queues, topics, or streams
- Defining event names, payload schemas, envelopes, headers, metadata, topic/channel naming, or partition keys
- Modeling producers, consumers, subscriptions, fan-out, choreography, orchestration, sagas, or process managers
- Planning schema evolution, event versioning, backward compatibility, deprecation, or replay behavior
- Designing idempotency, deduplication, ordering, retry, timeout, poison-message, and DLQ behavior
- Building producer/consumer contract tests or event compatibility checks
- Publishing event contracts to a developer portal, schema registry, event catalog, or internal platform
- Combining synchronous HTTP APIs with async events, such as REST command submission plus lifecycle events
- Designing AWS EventBridge, SNS/SQS, Kinesis, DynamoDB Streams, Kafka/MSK, RabbitMQ, MQTT, or webhook-based integrations where the contract matters

Pair with:

- `api-governance` for lifecycle checkpoints, audit evidence, publishing, and review gates
- `aws-serverless` for Lambda, EventBridge, API Gateway, Step Functions, event sources, and production readiness on AWS
- `aws-messaging-and-streaming` for AWS service selection across SQS, SNS, EventBridge, Kinesis, MSK, and Firehose
- `openapi-api-designer` when the API includes synchronous HTTP resources alongside events
- `graphql-api` or `grpc-api` when those contracts coexist with events
- `node-backend`, `spring-boot-engineer`, `go-builder`, or `python-dev` for implementation in a concrete runtime
- `test-driven-development` when adding producer/consumer tests before implementation

Do not use this skill as the only guide for:

- Pure REST/OpenAPI work with no async/event contract concerns
- Broker installation, networking, or cloud resource provisioning without contract design
- Low-level performance tuning of Kafka, Kinesis, RabbitMQ, or brokers; use platform-specific docs and skills
- Security-only exploit analysis unrelated to event contract design

## Core Design Principles

1. **Events are product interfaces**
   Treat events and streams as external contracts, not private implementation leakage. Consumers need stable names, schemas, examples, semantics, and change policies.

2. **Model domain facts before transport mechanics**
   Start with the business fact or intent. Broker details, topic names, and Lambda triggers come later.

3. **Separate commands from events**
   A command asks for work to happen. An event says something already happened. Confusing them creates brittle workflows and unclear ownership.

4. **Design for independent consumers**
   Producers should not encode assumptions about every current consumer. The contract should support future consumers where appropriate without becoming a vague data dump.

5. **Make delivery semantics explicit**
   At-least-once delivery, retries, deduplication windows, ordering guarantees, replay windows, and DLQ behavior are part of the API.

6. **Schema evolution is a first-class requirement**
   Event contracts live longer than individual services. Prefer additive changes, compatibility checks, and deprecation paths over breaking rewrites.

7. **Observability belongs in the contract conversation**
   Correlation IDs, causation IDs, trace context, event IDs, timestamps, source identifiers, and business keys determine whether async systems can be debugged.

## Design Workflow

### 1. Frame the API product and consumers

Before drafting events, answer:

- What business capability or process does this event API expose?
- Who produces each event or command?
- Who consumes it now, and who might consume it later?
- Is the consumer internal, partner, public, or regulated?
- Is this API for notifications, workflow coordination, task distribution, analytics, event sourcing, CDC, or integration?
- What latency, ordering, reliability, retention, and replay expectations matter?

If these are unclear, pause and use `api-governance` before choosing a broker or writing AsyncAPI.

### 2. Classify the interaction pattern

Use the smallest fitting pattern:

| Pattern | Use when | Contract focus |
|---|---|---|
| Domain event | A business fact occurred and many consumers may react | Past-tense name, immutable fact, source, subject, schema evolution |
| Command message | One component requests another to do work | Intent, target owner, validation errors, idempotency key, timeout behavior |
| Notification | Consumers need to know something changed but may fetch details elsewhere | Minimal payload, resource links, freshness, authorization boundary |
| Event stream | Consumers need ordered/replayable records over time | Partition key, offset, retention, replay, ordering, schema compatibility |
| Queue/task | Work must be distributed among competing workers | visibility timeout, retry, DLQ, idempotency, poison message handling |
| Webhook | External receiver gets pushed events over HTTP | subscription model, signing, retry, backoff, delivery logs, challenge/verification |
| Request/reply async | Response is asynchronous or long-running | correlation ID, response channel, timeout, state transitions |
| Saga/process event | Multi-step workflow crosses service boundaries | orchestration/choreography choice, compensation, state machine visibility |

Avoid using a stream when a queue is enough, a queue when a direct API is enough, or generic events when a command has one clear owner.

### 3. Model events and messages

For each candidate event/message, define:

- **Name:** stable, domain-oriented, and convention-driven
- **Type:** event, command, notification, stream record, webhook event, or reply
- **Producer:** owning service/domain/team
- **Consumers:** known consumers and consumer class, without overfitting payloads to them
- **Trigger:** what causes emission
- **Meaning:** exact business fact or requested action
- **Payload:** required fields, optional fields, schemas, examples, and sensitive data classification
- **Metadata:** event ID, type, source, subject, timestamp, content type, schema version, trace/correlation data
- **Delivery semantics:** at-least-once/exactly-once illusion, ordering, duplicate behavior, retry and DLQ policy
- **Retention/replay:** whether events can be replayed and for how long
- **Compatibility:** additive change rules, versioning, deprecation, and consumer migration plan

### 4. Choose envelope and schema strategy

Prefer an explicit envelope over ad hoc headers and random payload metadata.

A portable CloudEvents-style envelope usually includes:

- `id` — unique event identifier for deduplication and traceability
- `source` — producer/source URI or stable identifier
- `type` — event type, often reverse-DNS or domain-qualified
- `specversion` — CloudEvents spec version when using CloudEvents
- `time` — occurrence or publication timestamp; define which one
- `subject` — business subject/resource where useful
- `datacontenttype` — payload media type, commonly `application/json`
- `dataschema` — schema URI where available
- `data` — domain payload

Add domain metadata deliberately:

- `correlationId` for end-to-end request/workflow correlation
- `causationId` for the event or command that caused this event
- `traceparent`/trace context where distributed tracing is used
- `tenantId` only when multi-tenant isolation requires it and policy allows it
- `partitionKey` only when transport or ordering strategy needs it

Do not put secrets, credentials, access tokens, or excessive PII in event payloads or metadata. Events are often retained, replayed, logged, and forwarded more broadly than synchronous request data.

### 5. Define names, channels, topics, and ownership

Naming should reveal domain meaning and operational boundaries.

Event type conventions:

- Prefer past-tense facts: `order.created`, `payment.authorized`, `shipment.dispatched`
- Use commands for imperatives: `CreateOrder`, `AuthorizePayment`, or a house-style command name
- Avoid vague names: `data.updated`, `notification.sent`, `process.event`
- Avoid leaking implementation: `database.row.inserted` unless this is explicitly CDC

Channel/topic conventions:

- Make ownership and environment strategy explicit
- Avoid one mega-topic with unrelated event types unless the platform intentionally uses event type filtering
- Avoid one topic per tiny event when operational overhead outweighs clarity
- For ordered streams, document the partition key and what ordering it guarantees
- For cross-account/cross-domain buses, document trust boundaries and publication permissions

### 6. Draft or review the AsyncAPI contract

When using AsyncAPI, ensure the document captures both human intent and machine-checkable structure.

Minimum useful AsyncAPI content:

- `info.title`, `info.version`, and `info.description`
- `servers` with protocol, URL placeholders, and environment descriptions
- channels or addressable topics/queues/routes
- operations that show publish/subscribe direction clearly
- messages with names, titles, summaries, descriptions, examples, and payload schemas
- shared components for schemas, messages, security schemes, parameters, and correlation IDs
- bindings where the broker/protocol requires important details
- security schemes and operation/channel-level security where applicable
- tags or grouping by business capability

For each message, check:

- Does the name describe the public contract, not an internal class?
- Is the producer/consumer direction unambiguous?
- Does the payload schema include descriptions and realistic examples?
- Are event metadata/envelope fields documented?
- Are required and optional fields clear?
- Are nullability and default semantics explicit?
- Is schema versioning and compatibility policy visible?

### 7. Design compatibility and versioning

Default to backward-compatible evolution:

- Add optional fields instead of changing meanings or removing fields
- Never reuse an event type name for incompatible semantics
- Do not change the type, unit, format, or meaning of an existing field without a new version
- Keep enum expansion compatibility in mind; consumers may reject unknown enum values
- Prefer tolerant readers and explicit unknown-field behavior
- Version schemas and messages intentionally; avoid versioning every tiny additive change in the event type name
- Provide deprecation windows and consumer migration guidance for breaking changes

Breaking changes include:

- removing a field consumers may use
- making optional fields required
- changing field meaning, unit, format, or cardinality
- changing event timing or business semantics
- changing ordering, retention, retry, or deduplication guarantees
- changing channel/topic location without a migration bridge

### 8. Specify reliability behavior

Async APIs fail differently from request/response APIs. The contract should answer:

- Can the same event be delivered more than once?
- How should consumers deduplicate events?
- Which field is the idempotency or event ID key?
- What ordering is guaranteed, and at what scope?
- What happens when a consumer fails repeatedly?
- Is there a DLQ, parking lot, replay topic, or manual remediation workflow?
- How long are messages retained?
- Can consumers replay historical events?
- Are retries immediate, exponential, scheduled, or broker-managed?
- Are poison messages isolated from healthy traffic?

For command messages, also define:

- timeout behavior
- accepted/rejected response semantics
- validation failure format
- idempotency requirements
- whether commands may be retried safely

### 9. Plan observability and operations

Every event-driven API should define enough metadata and operational evidence for debugging.

Minimum observability expectations:

- correlation ID across sync and async boundaries
- event ID and producer identity in logs
- consumer lag/backlog metrics where applicable
- publish success/failure metrics
- retry and DLQ metrics
- schema validation failures
- consumer processing errors by event type
- trace propagation where supported
- dashboards or runbooks for stuck workflows and poison messages

For AWS, pair with `aws-observability`, `aws-serverless`, and `aws-messaging-and-streaming` to turn these into CloudWatch, X-Ray/ADOT, EventBridge, Lambda, SQS, SNS, Kinesis, or MSK-specific checks.

### 10. Test the contract before implementation drifts

Use producer and consumer contract tests where possible.

Recommended checks:

- AsyncAPI parses and references resolve
- message examples validate against schemas
- producer output validates against the published schema
- consumer fixtures include old, current, and forward-compatible events
- incompatible schema changes fail CI
- duplicate delivery is tested
- out-of-order delivery is tested when ordering is not guaranteed
- DLQ/poison-message handling is tested
- replay or redrive scenarios are tested
- webhook signing/retry behavior is tested where applicable

Do not only test the happy path handler. Most async production defects happen around retries, duplicates, ordering, and poison messages.

## Common Architecture Decisions

### Choreography vs orchestration

Use choreography when independent services can react to facts without a central coordinator and the process remains understandable. Use orchestration when a workflow needs explicit state, timeouts, compensation, human visibility, or strict sequencing.

If using AWS, Step Functions often fits explicit orchestration, while EventBridge/SNS/Kafka-style events fit choreography and fan-out. Document the decision and the failure behavior either way.

### Event notification vs event-carried state transfer

A notification event says “something changed; fetch the latest state elsewhere.” Event-carried state transfer includes enough data for consumers to act without a follow-up call.

Choose notification when authorization boundaries, payload size, or freshness make fetch-after-notify safer. Choose event-carried state when consumers need autonomy, audit trails, replay, or lower coupling to the producer API.

### Event sourcing vs event integration

Event sourcing uses events as the system of record for state reconstruction. Event integration uses events to communicate between systems. Do not apply event-sourcing complexity unless the domain and audit/replay needs justify it.

### Queue vs stream

Use a queue for competing workers and task distribution. Use a stream when multiple independent consumers need replayable ordered records. A stream can support messaging-like workloads, but it adds partitioning and retention design concerns.

### Webhooks as event APIs

For webhooks, define:

- subscription creation and deletion API
- event type filtering
- signing algorithm and key rotation
- retry schedule and maximum delivery attempts
- delivery log access
- challenge/verification flow
- endpoint timeout expectations
- payload schema and versioning
- replay/manual resend behavior

Pair with `openapi-api-designer` for the subscription management HTTP API and this skill for webhook event contracts.

## Event Contract Review Checklist

For each event/message/channel, verify:

- [ ] The business meaning is clear and stable
- [ ] The producer and owning domain are explicit
- [ ] Known consumer classes are identified without overfitting the payload
- [ ] The interaction type is correct: event, command, notification, queue task, stream record, webhook, or reply
- [ ] The name follows a consistent convention
- [ ] The envelope and metadata are documented
- [ ] Event ID, source, type, timestamp, and content type are present or intentionally omitted
- [ ] Correlation/causation/trace fields are defined where workflows cross boundaries
- [ ] Payload schema has descriptions, required fields, examples, and sensitive data review
- [ ] Topic/channel naming and ownership are documented
- [ ] Ordering, partitioning, retention, replay, and delivery guarantees are explicit
- [ ] Retry, idempotency, duplicate, and DLQ behavior are explicit
- [ ] Compatibility and versioning policy is documented
- [ ] Contract tests or schema compatibility checks are planned
- [ ] Observability signals and runbook expectations are defined
- [ ] Publication/discovery path is clear, such as event catalog, schema registry, or developer portal

## Common Pitfalls

1. **Treating events as private implementation details**
   Consumers build against events. If an event leaves a service boundary, it needs contract discipline.

2. **Naming events after CRUD or database mechanics**
   `customer.updated` is often too vague. Prefer domain-specific facts such as `customer.email-address-verified` when that distinction matters.

3. **Publishing generic data blobs**
   A flexible JSON blob without schema, examples, and meaning shifts integration burden to every consumer.

4. **Confusing commands and events**
   `OrderCreateRequested` and `OrderCreated` mean different things. Mixing them leads to incorrect retries, ownership, and user expectations.

5. **Ignoring duplicate delivery**
   Most systems provide at-least-once delivery. Consumers must be idempotent unless the platform truly guarantees otherwise and the limitation is documented.

6. **Assuming ordering globally**
   Ordering is usually per partition key, message group, shard, or stream. State the scope exactly.

7. **Forgetting poison-message paths**
   Retries without DLQ/remediation can block queues, create retry storms, or hide data loss.

8. **Breaking consumers with “minor” schema changes**
   Renaming a field, changing units, tightening enum values, or making a field required can be a breaking API change.

9. **Skipping observability until production**
   Async failures are hard to diagnose without correlation IDs, event IDs, lag/backlog metrics, and DLQ visibility.

10. **Choosing infrastructure before contract shape**
   Broker choice matters, but it should follow interaction semantics, retention/replay needs, throughput, ordering, and consumer model.

## Verification Checklist

- [ ] The event-driven API purpose, consumers, and owning domains are clear
- [ ] Commands, events, streams, queues, webhooks, and notifications are not conflated
- [ ] AsyncAPI or an equivalent contract artifact exists for asynchronous interfaces
- [ ] CloudEvents or a comparable envelope strategy is documented when cross-system portability matters
- [ ] Event names, channels/topics, schemas, examples, and metadata are consistent
- [ ] Delivery semantics, idempotency, ordering, retries, DLQs, retention, and replay are explicit
- [ ] Schema evolution and deprecation rules are defined before publication
- [ ] Contract tests and compatibility checks are part of CI or the delivery plan
- [ ] Observability and operational runbooks cover async failure modes
- [ ] The design is paired with platform-specific skills before provisioning or implementation
