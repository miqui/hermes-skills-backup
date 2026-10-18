# Observability — Micrometer, Metrics, Tracing & Structured Logging

> Reference for: Spring Boot Engineer
> Load when: Configuring Micrometer metrics, OTLP/Prometheus export, distributed tracing, structured logging, custom meters, health indicators, or audit events

## Overview

Spring Boot 3.x ships with Micrometer 1.12+ and Micrometer Tracing as the default observability stack. Actuator exposes metrics, health, and info endpoints. This reference covers production-grade configuration for metrics, tracing, and structured logging — not just "Actuator is on."

## Dependencies

```xml
<!-- pom.xml — pick the registry/registries you need -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
<!-- OTLP export (metrics + traces) -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-otlp</artifactId>
</dependency>
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-exporter-otlp</artifactId>
</dependency>
<!-- Distributed tracing bridge -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
```

```yaml
# build.gradle.kts
implementation("org.springframework.boot:spring-boot-starter-actuator")
implementation("io.micrometer:micrometer-registry-prometheus")
implementation("io.micrometer:micrometer-registry-otlp")
implementation("io.opentelemetry:opentelemetry-exporter-otlp")
implementation("io.micrometer:micrometer-tracing-bridge-otel")
```

## Actuator Configuration

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,loggers
      base-path: /actuator
  endpoint:
    health:
      show-details: when-authorized   # don't expose internal details to anonymous
      probes:
        enabled: true                  # k8s liveness/readiness
      group:
        liveness:
          include: livenessState
        readiness:
          include: readinessState,db
  health:
    livenessState:
      enabled: true
    readinessState:
      enabled: true
  metrics:
    tags:
      application: ${spring.application.name}
      environment: ${spring.profiles.active:default}
    distribution:
      percentiles-histogram:
        http.server.requests: true
      percentiles:
        http.server.requests: 0.5, 0.95, 0.99
      slo:
        http.server.requests: 50ms, 100ms, 200ms, 500ms, 1000ms
  tracing:
    sampling:
      probability: 1.0   # 100% in dev; lower in prod to control cost
  otlp:
    metrics:
      export:
        url: http://otel-collector:4318/v1/metrics
        step: 30s
        enabled: true
    tracing:
      export:
        url: http://otel-collector:4318/v1/traces
        enabled: true
  prometheus:
    metrics:
      export:
        enabled: true
        step: 30s
```

## Custom Meters

### Counter — event count

```java
@Service
@RequiredArgsConstructor
public class OrderMetrics {
    private final MeterRegistry meterRegistry;

    private Counter ordersCreated;
    private Counter ordersFailed;

    @PostConstruct
    void initMeters() {
        ordersCreated = Counter.builder("orders.created")
            .description("Number of orders successfully created")
            .tag("type", "standard")
            .register(meterRegistry);

        ordersFailed = Counter.builder("orders.failed")
            .description("Number of order creation failures")
            .register(meterRegistry);
    }

    public void recordCreated() { ordersCreated.increment(); }
    public void recordFailed()  { ordersFailed.increment(); }
}
```

### Timer — duration tracking

```java
public class CheckoutService {
    private final MeterRegistry meterRegistry;

    public CheckoutResult checkout(Long orderId) {
        return Timer.builder("checkout.duration")
            .description("Checkout processing time")
            .tag("paymentMethod", "card")
            .register(meterRegistry)
            .record(() -> {
                // ... checkout logic
                return result;
            });
    }

    // Or manual start/stop
    public CheckoutResult checkoutManual(Long orderId) {
        Timer.Sample sample = Timer.start(meterRegistry);

        try {
            CheckoutResult result = doCheckout(orderId);
            sample.stop(Timer.builder("checkout.duration")
                .tag("outcome", "success")
                .register(meterRegistry));
            return result;
        } catch (Exception e) {
            sample.stop(Timer.builder("checkout.duration")
                .tag("outcome", "failure")
                .register(meterRegistry));
            throw e;
        }
    }
}
```

### Gauge — instantaneous value

```java
@Service
public class QueueDepthMetrics {
    private final TaskExecutor queue;

    @PostConstruct
    void initGauge() {
        meterRegistry.gauge("queue.depth", queue, q -> q.getActiveCount());
    }
}
```

### Multi-dimensional tags — cardinality caution

```java
// GOOD — bounded cardinality (HTTP status code, route template)
Timer.builder("http.server.requests")
    .tag("status", String.valueOf(response.getStatusCode()))
    .tag("uri", request.getRequestURI())  // use template, not raw URI
    .tag("method", request.getMethod())
    .register(meterRegistry);

// BAD — unbounded cardinality
Timer.builder("http.server.requests")
    .tag("uri", request.getRequestURI())           // raw URI: /users/12345, /users/67890...
    .tag("userId", principal.getName())             // N tags per user
    .register(meterRegistry);
```

### @Counted and @Timed annotations

```java
@Service
public class ProductService {

    @Counted(value = "product.search", extraTags = {"type", "by-category"})
    public List<Product> searchByCategory(String category) { ... }

    @Timed(value = "product.fetch", extraTags = {"source", "cache"},
           percentiles = {0.5, 0.95, 0.99})
    public Product fetchProduct(Long id) { ... }
}
```

## Distributed Tracing

### Manual spans

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    private final Tracer tracer;
    private final OrderRepository orderRepository;

    public Order processOrder(OrderRequest request) {
        Span span = tracer.nextSpan().name("processOrder").start();
        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            span.tag("order.type", request.type());
            span.tag("order.items", String.valueOf(request.items().size()));

            Order order = createOrder(request);

            span.event("order.created");
            return order;
        } catch (Exception e) {
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }
}
```

### Correlation ID for non-traced HTTP clients

```java
@Component
public class CorrelationIdFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        MDC.put("correlationId", UUID.randomUUID().toString());
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.clear();
        }
    }
}
```

### Trace context propagation via WebClient

```java
@Configuration
public class TracingClientConfig {

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder()
            .filter((request, next) -> {
                // Micrometer Tracing propagates trace context automatically
                // when the instrumented WebClient is used
                return next.exchange(request);
            });
    }
}
```

## Structured Logging

### Logback JSON (logstash-encoder)

```xml
<!-- pom.xml -->
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.4</version>
</dependency>
```

```xml
<!-- logback-spring.xml -->
<configuration>
    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

    <springProfile name="!local">
        <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
            <encoder class="net.logstash.logback.encoder.LogstashEncoder">
                <includeMdcKeyName>correlationId</includeMdcKeyName>
                <includeMdcKeyName>traceId</includeMdcKeyName>
                <includeMdcKeyName>spanId</includeMdcKeyName>
                <includeMdcKeyName>userId</includeMdcKeyName>
                <customFields>{"app":"${spring.application.name:-app}"}</customFields>
            </encoder>
        </appender>
        <root level="INFO">
            <appender-ref ref="JSON"/>
        </root>
    </springProfile>

    <springProfile name="local">
        <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
            <encoder>
                <pattern>%d{HH:mm:ss} %-5level [%thread] %logger{36} - %msg%n</pattern>
            </encoder>
        </appender>
        <root level="DEBUG">
            <appender-ref ref="CONSOLE"/>
        </root>
    </springProfile>
</configuration>
```

### Structured log fields

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {
    private final OrderRepository orderRepository;

    public Order createOrder(OrderRequest request) {
        // Use MDC for contextual fields that the encoder includes automatically
        MDC.put("orderId", request.orderId());
        MDC.put("userId", request.userId());

        try {
            Order order = orderRepository.save(buildOrder(request));
            log.info("order_created orderId={} userId={} total={}",
                order.getId(), order.getUserId(), order.getTotal());
            return order;
        } catch (Exception e) {
            log.error("order_creation_failed orderId={} userId={} error={}",
                request.orderId(), request.userId(), e.getMessage(), e);
            throw e;
        } finally {
            MDC.remove("orderId");
            MDC.remove("userId");
        }
    }
}
```

### Log output shape

```json
{
  "@timestamp": "2026-08-18T14:23:01.482Z",
  "level": "INFO",
  "logger": "com.example.app.service.OrderService",
  "thread": "http-nio-8080-exec-1",
  "message": "order_created orderId=12345 userId=67890 total=99.50",
  "app": "order-service",
  "traceId": "a1b2c3d4e5f6a7b8",
  "spanId": "a1b2c3d4",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "orderId": "12345",
  "userId": "67890"
}
```

## Custom Health Indicators

```java
@Component
@RequiredArgsConstructor
public class ExternalApiHealthIndicator implements HealthIndicator {

    private final ExternalApiClient apiClient;

    @Override
    public Health health() {
        try {
            ApiHealthResponse status = apiClient.checkHealth();
            if (status.isHealthy()) {
                return Health.up()
                    .withDetail("provider", status.getProvider())
                    .withDetail("latencyMs", status.getLatencyMs())
                    .build();
            } else {
                return Health.down()
                    .withDetail("provider", status.getProvider())
                    .withDetail("reason", status.getError())
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .withDetail("exception", e.getClass().getSimpleName())
                .build();
        }
    }
}
```

## Kubernetes Probes

```java
// Liveness — should the pod be restarted?
@Component
public class LivenessHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        // Check if the application is in a state where it can serve requests
        // Return DOWN only if the app is in an unrecoverable state
        return Health.up().build();
    }
}

// Readiness — should the pod receive traffic?
@Component
@RequiredArgsConstructor
public class ReadinessHealthIndicator implements HealthIndicator {
    private final DataSource dataSource;
    private final RedisConnectionFactory redisConnectionFactory;

    @Override
    public Health health() {
        Health.Builder builder = Health.up();
        try (Connection conn = dataSource.getConnection()) {
            if (!conn.isValid(2)) {
                builder.down().withDetail("database", "unreachable");
            }
        } catch (SQLException e) {
            builder.down().withDetail("database", e.getMessage());
        }
        try (RedisConnection redis = redisConnectionFactory.getConnection()) {
            redis.ping();
        } catch (Exception e) {
            builder.down().withDetail("redis", e.getMessage());
        }
        return builder.build();
    }
}
```

```yaml
management:
  endpoint:
    health:
      group:
        readiness:
          include: readinessState,readinessHealthIndicator
        liveness:
          include: livenessState,livenessHealthIndicator
```

## Graceful Shutdown

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        new SpringApplicationBuilder(Application.class)
            .web(WebApplicationType.SERVLET)
            .bannerMode(Banner.Mode.OFF)
            .registerShutdownHook(true)
            .run(args);
    }
}
```

```yaml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
management:
  endpoint:
    health:
      probes:
        enabled: true  # enables liveness/readiness groups
```

## Audit Events

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class AuditEventService {
    private final MeterRegistry meterRegistry;

    public void recordAuthorizationDecision(
            String principalId, String action, String resourceType,
            String resourceId, boolean allowed, String reason) {

        // Structured log
        log.info("authorization_decision principal={} action={} resource={}:{} allowed={} reason={}",
            principalId, action, resourceType, resourceId, allowed, reason);

        // Metric
        Counter.builder("authorization.decisions")
            .tag("action", action)
            .tag("outcome", allowed ? "allow" : "deny")
            .tag("reason", reason)
            .register(meterRegistry)
            .increment();
    }
}
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Event count | `Counter` | Monotonically increasing |
| Duration | `Timer` | Histogram + percentiles via `percentiles-histogram` |
| Instantaneous value | `Gauge` | Use for queue depth, cache size, active threads |
| Long task duration | `@Timed` / `LongTaskTimer` | For async/in-flight operations |
| Custom metrics | `MeterRegistry` | Inject and register in `@PostConstruct` |
| Distributed traces | `Tracer` / `Span` | Micrometer Tracing bridges to OTel/Brave |
| Trace propagation | Auto-instrumented | WebClient, RestTemplate, Kafka listener |
| Structured logs | logstash-encoder + MDC | JSON output with traceId/spanId fields |
| Health checks | `HealthIndicator` | Custom indicators auto-registered |
| K8s probes | liveness/readiness groups | `management.endpoint.health.probes.enabled` |
| Graceful shutdown | `server.shutdown: graceful` | Drains in-flight requests before stopping |

## Common Pitfalls

1. **High-cardinality tags.** Tagging by `userId`, raw `URI`, or `requestId` creates unbounded label combinations that exhaust memory in the metrics backend and make dashboards unreadable. Use bounded tags (HTTP method, status code class, route template).

2. **100% trace sampling in production.** At scale, 100% sampling generates enormous trace volumes and backend costs. Use head-based sampling (0.1–10%) in prod and tail-based sampling at the collector for error/latency-rich traces.

3. **Forgetting to register meters.** Calling `Counter.builder(...)` without `.register(meterRegistry)` returns a no-op counter. Always chain `.register()`.

4. **Mixing Micrometer and Prometheus native APIs.** Use Micrometer's abstraction — direct `io.prometheus.client` usage bypasses the registry lifecycle and can cause duplicate registration errors.

5. **Exposing Actuator endpoints without auth in production.** `management.endpoints.web.exposure.include=*` in prod leaks env vars, heap dumps, and thread dumps. Restrict to `health,info,metrics,prometheus` and protect with Spring Security.

6. **Not using percentiles-histogram.** Without `percentiles-histogram: true`, percentile calculations are client-side approximations that are less accurate and cannot be aggregated across instances. Enable it for SLO-critical timers.

7. **Blocking in health indicators.** A health indicator that makes a slow HTTP call to a downstream service can cause the K8s readiness probe to timeout, cycling pods. Use short timeouts and cache the result.

8. **Losing trace context across async boundaries.** `@Async` and `CompletableFuture` can lose the trace context. Use `ContextSnapshot` or instrument the executor, or prefer virtual threads which preserve context.

9. **Structured logs without trace correlation.** JSON logs without `traceId`/`spanId` fields cannot be correlated with distributed traces. Ensure the logback encoder includes MDC keys for tracing.

10. **Not testing observability.** Metrics, traces, and health indicators are production features. Write a `@WebMvcTest` or `@SpringBootTest` that verifies custom meters are registered and health endpoints return expected status.
