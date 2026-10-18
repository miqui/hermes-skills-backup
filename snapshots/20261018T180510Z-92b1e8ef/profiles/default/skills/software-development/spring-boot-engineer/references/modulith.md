# Spring Modulith — Modular Monolith Architecture

> Reference for: Spring Boot Engineer
> Load when: Structuring a Spring Boot application as a modular monolith, verifying module boundaries, externalizing module events, or testing modules in isolation

## Overview

Spring Modulith provides a structured approach to organizing a Spring Boot application as a modular monolith. It enables developers to organize functionality into modules with explicit boundaries, verifiable dependencies, and event-driven communication — without the operational complexity of microservices.

Key ideas:
- **Module-by-package** convention — each module is a top-level package
- **Explicit dependencies** — modules declare what they depend on
- **Event-driven communication** — modules communicate via Spring ApplicationEvents
- **Verifiable boundaries** — a test verifies that modules do not access internals of other modules
- **Documentation** — module structure can be documented as AsciiDoc or PlantUML diagrams

## Dependencies

```xml
<dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-core</artifactId>
</dependency>

<!-- For event externalization (Kafka, AMQP, etc.) -->
<dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-jdbc</artifactId>
</dependency>
```

```kotlin
// build.gradle.kts
implementation("org.springframework.modulith:spring-modulith-starter-core")
implementation("org.springframework.modulith:spring-modulith-starter-jdbc")
```

## Module Structure

### Package-by-module convention

```text
src/main/java/com/example/app/
  order/                    ← "order" module
    Order.java
    OrderService.java
    OrderController.java
    OrderRepository.java
    OrderManagement.java    ← named interface (public API)
    internal/               ← internal types, not accessible from outside
      OrderInternalService.java
  inventory/                ← "inventory" module
    InventoryService.java
    StockItem.java
    internal/
      InventoryInternal.java
  shipment/                 ← "shipment" module
    ShipmentService.java
    Shipment.java
  Application.java          ← root of the application
```

### Named Interface

By default, types in a module's root package are considered public API. Types in `internal` sub-packages are internal and should not be accessed by other modules.

```java
// com.example.app.order — PUBLIC API (accessible from other modules)
public interface OrderManagement {
    Order createOrder(OrderRequest request);
    Optional<Order> findById(Long id);
}

// com.example.app.order.internal — INTERNAL (not accessible)
@Service
public class OrderInternalService {
    // implementation details
}
```

### @ApplicationModule annotation

```java
@org.springframework.modulith.ApplicationModule(
    displayName = "Order Management",
    allowedDependencies = { "inventory", "shipment" }
)
package com.example.app.order;
```

The `allowedDependencies` list declares which other modules this module can depend on. Any access to a module not listed here will cause a verification failure.

### NamedInterface annotation

```java
@org.springframework.modulith.NamedInterface
public interface OrderManagement { ... }

// Can also be applied at package level
@org.springframework.modulith.NamedInterface
package com.example.app.order;
```

## Module Dependency Verification

### ModulithVerifier

```java
@SpringBootTest
class ModulithVerificationTest {

    @Test
    void verifyModularStructure() {
        ApplicationModules.of(Application.class).verify();
    }
}
```

This test verifies:
- No module accesses internals of another module
- No module depends on a module not listed in `allowedDependencies`
- All public API is via the named interface, not direct access to internal types

### AssertableModulith

```java
@SpringBootTest
class ModulithStructureTest {

    @Test
    void assertModuleStructure() {
        ApplicationModules modules = ApplicationModules.of(Application.class);

        AssertableModulith assertable = AssertableModulith.of(modules);

        // Verify module exists
        assertThat(assertable.module("order")).isPresent();

        // Verify dependencies
        assertThat(assertable.module("order").dependencies())
            .containsExactlyInAnyOrder("inventory", "shipment");

        // Verify events
        assertThat(assertable.module("order").events())
            .contains("OrderCreated", "OrderCancelled");
    }
}
```

## Event-Driven Communication

### Publishing domain events

```java
// com.example.app.order
@Service
@RequiredArgsConstructor
public class OrderService {
    private final ApplicationEventPublisher eventPublisher;
    private final OrderRepository orderRepository;

    @Transactional
    public Order createOrder(OrderRequest request) {
        Order order = Order.builder()
            .customerId(request.customerId())
            .total(request.total())
            .status(OrderStatus.PENDING)
            .build();

        order = orderRepository.save(order);

        // Publish domain event — other modules can listen
        eventPublisher.publishEvent(new OrderCreated(
            order.getId(),
            order.getCustomerId(),
            order.getTotal(),
            Instant.now()
        ));

        return order;
    }
}

public record OrderCreated(Long orderId, Long customerId, BigDecimal total, Instant occurredAt) {}
```

### Listening to events from other modules

```java
// com.example.app.inventory
@Service
@RequiredArgsConstructor
public class InventoryService {
    private final OrderManagement orderManagement;

    @TransactionalEventListener
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void onOrderCreated(OrderCreated event) {
        reserveStock(event.orderId(), event.total());
    }
}
```

### Event Externalization

Spring Modulith can externalize domain events to external systems (Kafka, RabbitMQ, SQS, etc.) using `@Externalized`.

```java
@Externalized("order.created::{ orderId }")
public record OrderCreated(Long orderId, Long customerId, BigDecimal total, Instant occurredAt) {}
```

This publishes the event to a message broker with:
- Routing key: `order.created.<orderId>`
- Payload: serialized `OrderCreated` record

### Event externalization with completion

```java
@Externalized(
    value = "order.created::{ orderId }",
    source = "order"  // the module publishing the event
)
public record OrderCreated(Long orderId, Long customerId, BigDecimal total, Instant occurredAt) {}
```

### Externalized with condition

```java
@Externalized(
    value = "order.created::{ orderId }",
    condition = "#this.total > 1000"  // only externalize orders above threshold
)
public record OrderCreated(Long orderId, Long customerId, BigDecimal total, Instant occurredAt) {}
```

### ApplicationModuleListener

```java
@org.springframework.modulith.ApplicationModuleListener
public class InventoryOrderListener {
    @TransactionalEventListener
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void onOrderCreated(OrderCreated event) {
        // Handle event
    }
}
```

`@ApplicationModuleListener` restricts which modules can receive the event, ensuring event flow stays within the module dependency graph.

## Testing Modules

### @ApplicationModuleTest

```java
@ApplicationModuleTest
class OrderModuleTest {

    @Autowired
    private OrderManagement orderManagement;

    @MockBean
    private OrderRepository orderRepository;

    @Test
    void shouldCreateOrder() {
        when(orderRepository.save(any(Order.class)))
            .thenAnswer(inv -> inv.getArgument(0));

        Order order = orderManagement.createOrder(
            new OrderRequest(1L, BigDecimal.valueOf(99.50))
        );

        assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
    }
}
```

`@ApplicationModuleTest` boots only the `order` module and its declared dependencies, creating a narrow test context — similar to `@WebMvcTest` or `@DataJpaTest` but at the module level.

### Module-specific test configuration

```java
@ApplicationModuleTest
@Import(TestConfig.class)
class OrderModuleIntegrationTest {

    @Autowired
    private OrderManagement orderManagement;

    @Test
    void shouldPublishOrderCreatedEvent() {
        // Verify event was published
        var events = ApplicationModuleTest.of(Application.class)
            .and().publishEvent(new OrderCreated(1L, 1L, BigDecimal.TEN, Instant.now()))
            .and().verify();
    }
}
```

### Testing event flow across modules

```java
@SpringBootTest
class OrderInventoryEventFlowTest {

    @Autowired
    private OrderManagement orderManagement;

    @Autowired
    private InventoryService inventoryService;

    @Test
    void orderCreatedShouldReserveStock() {
        // Create order — triggers OrderCreated event
        orderManagement.createOrder(new OrderRequest(1L, BigDecimal.TEN));

        // Verify inventory was reserved
        verify(inventoryService).reserveStock(any(), any());
    }
}
```

## Module Documentation

### Documenter

```java
@SpringBootTest
class ModuleDocumentationTest {

    @Test
    void generateModuleDocumentation() {
        ApplicationModules modules = ApplicationModules.of(Application.class);

        new Documenter(modules)
            .writeModulesAsPlantUml()
            .writeIndividualModulesAsPlantUml()
            .writeAggregatingDocument();
    }
}
```

Output is generated under `target/spring-modulith-docs/`:
- `modules.puml` — PlantUML diagram of all modules and their dependencies
- `<module-name>.puml` — Individual module diagrams
- `aggregate.md` — AsciiDoc summary

### Module Canvas

```java
Documenter.DocumentationOptions options = Documenter.DocumentationOptions.defaults()
    .withOutputDirectory(Path.of("docs/modules"));

new Documenter(modules, options)
    .writeModuleCanvases()
    .writeAggregatingDocument();
```

The canvas includes:
- Module name and display name
- Dependency list
- Published events
- Consumed events
- Public API (named interfaces)
- Internal types summary

## Configuration

```yaml
spring:
  modulith:
    events:
      jdbc-schema:
        enabled: true        # create event publication log table
        schema: public       # schema for event tables
      completion-mode: update  # how completed events are handled
      republish-on-restart: true  # republish incomplete events on startup
```

### Event publication log

Spring Modulith uses a database table to track event publication state, ensuring at-least-once delivery even across restarts:

```sql
-- Auto-created by Spring Modulith
CREATE TABLE event_publication (
    id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event JSON NOT NULL,
    listener_id VARCHAR(255) NOT NULL,
    completion_date TIMESTAMP,
    publication_date TIMESTAMP NOT NULL
);
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Module declaration | `@ApplicationModule` | Applied at package level |
| Named interface | `@NamedInterface` | Public API of a module |
| Dependency verification | `ApplicationModules.of().verify()` | Run as a test |
| Event publication | `ApplicationEventPublisher` | Standard Spring events |
| Event externalization | `@Externalized` | Routes to broker |
| Module-scoped listener | `@ApplicationModuleListener` | Restricts event flow |
| Module test | `@ApplicationModuleTest` | Boots only the module |
| Structure assertions | `AssertableModulith` | Assertable module graph |
| Documentation | `Documenter` | PlantUML + AsciiDoc |
| Event log | `spring.modulith.events.jdbc-schema` | At-least-once delivery |

## Common Pitfalls

1. **Putting business logic in module root packages.** Types in the module root are public API by default. Keep implementation in `internal` sub-packages to prevent accidental coupling.

2. **Not running `ModulithVerifier` in CI.** Without the verification test, module boundary violations compile successfully but create hidden coupling. Run `ApplicationModules.of().verify()` as a CI gate.

3. **Circular module dependencies.** If module A depends on B and B depends on A, the verification will fail. Refactor to use events or extract shared types into a common module.

4. **Over-externalizing events.** Not every internal event needs to be externalized to a broker. Use `@Externalized` only for events that external systems or other bounded contexts need.

5. **Synchronous event handling defeating the purpose.** Using `@EventListener` (synchronous) instead of `@TransactionalEventListener(phase = AFTER_COMMIT)` couples modules at transaction time. Prefer async or `AFTER_COMMIT` phases for cross-module communication.

6. **Not testing event flow.** Events are the primary inter-module communication mechanism. Test that publishing an event triggers the expected listener behavior, including transaction boundaries.

7. **Direct database access across modules.** Modules should not share JPA entities or repositories. If module B needs data from module A, use A's named interface or an event — not direct repository access.

8. **Ignoring the event publication log.** If `spring.modulith.events.jdbc-schema.enabled=true`, the `event_publication` table accumulates completed events. Configure a cleanup or archival strategy for production.

9. **Using `@ApplicationModuleTest` when full context is needed.** Module tests boot only the module and its dependencies. If a test needs the full application context, use `@SpringBootTest` instead.

10. **Not documenting modules.** The `Documenter` generates valuable architecture diagrams and canvases. Run it as a test or build step and commit the output to the repo for onboarding and architecture reviews.
