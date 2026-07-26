# Observability Reference

## Observability Goals

Use observability to understand system behavior from the outside: what happened, where it happened, how often, and why. A healthy backend should make it easy to trace requests, detect failures, measure latency, and correlate logs with metrics and traces.

## Core Signals

Focus on the three pillars:
- logs for structured event detail
- metrics for rates, durations, and saturation
- traces for request flow across boundaries

## Logging Guidance

Prefer structured logs with stable field names such as:
- requestId
- userId (when appropriate and privacy-safe)
- route / operation name
- durationMs
- statusCode
- error code/class

Redact secrets and avoid logging sensitive payloads by default.

## Metrics Guidance

Track at least:
- request count
- error count
- latency percentiles
- queue/job throughput where relevant
- database and upstream dependency timings

Use labels carefully; high-cardinality labels can make metrics noisy and expensive.

## Tracing Guidance

Propagate request or trace IDs through HTTP calls, jobs, queues, and database boundaries where possible. Correlate traces with logs using shared identifiers.

### Targeted manual tracing for CLI or agent workflows

For small Node/TypeScript automation or agent-style backends, prefer **manual spans around the business actions you actually care about** before reaching for broad auto-instrumentation.

A good minimal pattern is:
- initialize a tracer provider explicitly
- use `ConsoleSpanExporter` when the requirement is console-only tracing
- wrap only meaningful actions such as `agent.run`, `agent.compose_notification`, or `agent.send_email`
- keep network/database/framework auto-instrumentation off when the requirement is "agent actions only"

This is especially useful for CLI apps where you want auditable spans without noisy trace output from every library call.

## Health and Readiness

Separate:
- liveness: process is running
- readiness: service can safely receive traffic
- dependency health: database/queue/cache/upstream status

Avoid making liveness checks depend on every downstream service.

## Error Reporting

Capture exceptions with enough context to diagnose them, but avoid leaking secrets, tokens, or full request bodies into logs and alerts.

## Alerting

Alert on user-impacting symptoms and sustained trends, not every transient blip. Good alerts are actionable and tied to SLOs or critical flows.

## Testing and Verification

Verify that:
- request IDs appear in logs
- failed requests emit useful structured errors
- latency and error metrics are visible
- tracing spans or equivalent request correlation exists for key flows

## Common Pitfalls

1. Logging too much raw payload data.
2. Using inconsistent field names across services.
3. Creating high-cardinality metrics labels.
4. Emitting logs without request correlation IDs.
5. Alerting on noise instead of actionable symptoms.
6. Enabling broad auto-instrumentation when the task only needs a few high-value spans for workflow steps.

## Checklist

- [ ] Logs are structured and redact sensitive data
- [ ] Metrics cover throughput, errors, and latency
- [ ] Request or trace IDs propagate through the stack
- [ ] Health/readiness checks are separated clearly
- [ ] Alerts are actionable and tied to important service behavior
