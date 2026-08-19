# Spring Apache Kafka — Producers, Consumers, Streams & Transactions

> Reference for: Spring Boot Engineer
> Load when: Integrating Kafka producers/consumers, configuring Kafka Streams, dead-letter topics, exactly-once semantics, or testing Kafka interactions

## Dependencies

```xml
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>

<!-- Kafka Streams -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka-test</artifactId>
    <scope>test</scope>
</dependency>
```

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      acks: all
      retries: 10
      properties:
        enable.idempotence: true
        max.in.flight.requests.per.connection: 5
        compression.type: lz4
    consumer:
      group-id: ${spring.application.name}
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      auto-offset-reset: earliest
      enable-auto-commit: false
      properties:
        spring.json.trusted.packages: "com.example.*"
    listener:
      ack-mode: manual_immediate
      concurrency: 3
```

## Producer

### KafkaTemplate

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderEventPublisher {
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public void publishOrderCreated(Order order) {
        ProducerRecord<String, Object> record = new ProducerRecord<>(
            "order-events",
            order.getId().toString(),   // key — same key goes to same partition
            new OrderCreatedEvent(order.getId(), order.getCustomerId(), order.getTotal(), Instant.now())
        );

        kafkaTemplate.send(record)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("publish_failed orderId={} topic={}", order.getId(), "order-events", ex);
                } else {
                    RecordMetadata meta = result.getRecordMetadata();
                    log.info("publish_ok orderId={} topic={} partition={} offset={}",
                        order.getId(), meta.topic(), meta.partition(), meta.offset());
                }
            });
    }
}
```

### Producer Configuration

```java
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        config.put(ProducerConfig.ACKS_CONFIG, "all");
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        config.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);
        config.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");
        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate(ProducerFactory<String, Object> pf) {
        return new KafkaTemplate<>(pf);
    }
}
```

## Consumer

### @KafkaListener

```java
@Service
@Slf4j
public class OrderEventConsumer {

    @KafkaListener(
        topics = "order-events",
        groupId = "inventory-service",
        concurrency = "3"
    )
    @Transactional
    public void handleOrderEvent(
            @Payload OrderCreatedEvent event,
            @Header(KafkaHeaders.RECEIVED_KEY) String key,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment ack
    ) {
        log.info("consume_ok topic=order-events key={} partition={} offset={}",
            key, partition, offset);

        try {
            processOrder(event);
            ack.acknowledge();
        } catch (Exception e) {
            log.error("consume_failed key={} error={}", key, e.getMessage(), e);
            // Don't ack — the record will be retried
            throw e;
        }
    }

    private void processOrder(OrderCreatedEvent event) {
        // Business logic
    }
}
```

### Consumer with retry and DLQ

```java
@Service
@Slf4j
@RequiredArgsConstructor
public class RetryableOrderConsumer {

    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final OrderProcessingService orderProcessingService;

    @KafkaListener(topics = "order-events", groupId = "order-processor")
    public void handle(OrderCreatedEvent event, Acknowledgment ack) {
        try {
            orderProcessingService.process(event);
            ack.acknowledge();
        } catch (RetryableException e) {
            // Retry to a retry topic with backoff based on attempt count
            int attempt = getRetryAttempt(event);
            if (attempt < MAX_RETRIES) {
                sendToRetryTopic(event, attempt);
                ack.acknowledge();
            } else {
                sendToDLQ(event, e);
                ack.acknowledge();
            }
        } catch (NonRetryableException e) {
            // Don't retry — send straight to DLQ
            sendToDLQ(event, e);
            ack.acknowledge();
        }
    }

    private void sendToRetryTopic(OrderCreatedEvent event, int attempt) {
        ProducerRecord<String, Object> record = new ProducerRecord<>(
            "order-events.retry",
            event.orderId().toString(),
            event
        );
        record.headers().add("retry-attempt", String.valueOf(attempt + 1).getBytes());
        kafkaTemplate.send(record);
    }

    private void sendToDLQ(OrderCreatedEvent event, Exception e) {
        ProducerRecord<String, Object> record = new ProducerRecord<>(
            "order-events.dlq",
            event.orderId().toString(),
            event
        );
        record.headers().add("error", e.getMessage().getBytes());
        record.headers().add("error-timestamp", Instant.now().toString().getBytes());
        kafkaTemplate.send(record);
    }
}
```

### Error Handler with DeadLetterPublishingRecoverer

```java
@Bean
public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory(
        ConsumerFactory<String, Object> consumerFactory,
        KafkaTemplate<String, Object> kafkaTemplate) {

    ConcurrentKafkaListenerContainerFactory<String, Object> factory =
        new ConcurrentKafkaListenerContainerFactory<>();
    factory.setConsumerFactory(consumerFactory);
    factory.getContainerProperties().setAckMode(AckMode.RECORD);

    // Default error handler with DLQ
    DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(
        kafkaTemplate,
        (record, ex) -> new TopicPartition(record.topic() + ".dlq", record.partition())
    );

    DefaultErrorHandler errorHandler = new DefaultErrorHandler(recoverer,
        new ExponentialBackOffWithMaxRetries(3));
    errorHandler.setCommitRecovered(true);
    errorHandler.setAckAfterHandle(true);

    factory.setCommonErrorHandler(errorHandler);
    return factory;
}
```

## Kafka Transactions (Exactly-Once Semantics)

### Producer-side transactions

```java
@Configuration
public class KafkaTransactionConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        config.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "order-tx-producer");
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        config.put(ProducerConfig.ACKS_CONFIG, "all");
        return new DefaultKafkaProducerFactory<>(config);
    }
}
```

### Consuming + producing in a transaction (consume-transform-produce)

```java
@Service
@RequiredArgsConstructor
public class TransactionalOrderProcessor {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @KafkaListener(topics = "orders.raw", groupId = "order-processor-tx")
    @Transactional
    public void process(RawOrderEvent event, Acknowledgment ack) {
        // This consume-transform-produce chain is atomic when:
        // 1. The consumer has isolation.level=read_committed
        // 2. The producer has a transactional.id
        // 3. The KafkaTemplate is transactional

        OrderProcessed processed = transform(event);
        kafkaTemplate.executeInTransaction(template -> {
            template.send("orders.processed", processed.id().toString(), processed);
            return null;
        });

        ack.acknowledge();
    }
}
```

```yaml
spring:
  kafka:
    consumer:
      properties:
        isolation.level: read_committed
    producer:
      transactional-id: order-tx-producer
```

## Kafka Streams

### Configuration

```yaml
spring:
  kafka:
    streams:
      application-id: order-streams
      properties:
        bootstrap.servers: localhost:9092
        processing.guarantee: exactly_once_v2
        state.dir: /tmp/kafka-streams
```

### Stream with KTable aggregation

```java
@Configuration
public class OrderStreamConfig {

    @Bean
    public KStream<String, OrderEvent> orderStream(StreamsBuilder builder) {
        KStream<String, OrderEvent> stream = builder.stream(
            "order-events",
            Consumed.with(Serdes.String(), JsonSerde.of(OrderEvent.class))
        );

        // Filter valid orders
        KStream<String, OrderEvent> validOrders = stream.filter(
            (key, value) -> value.status() == OrderStatus.CONFIRMED
        );

        // Group by category and aggregate total revenue
        KTable<String, Long> revenueByCategory = validOrders
            .groupBy((key, value) -> value.category(),
                Grouped.with(Serdes.String(), JsonSerde.of(OrderEvent.class)))
            .aggregate(
                () -> 0L,
                (key, value, aggregate) -> aggregate + value.amount().longValue(),
                Materialized.<String, Long, KeyValueStore<Bytes, byte[]>>as("revenue-by-category")
                    .withKeySerde(Serdes.String())
                    .withValueSerde(Serdes.Long())
            );

        // Write results to output topic
        revenueByCategory.toStream().to(
            "revenue-by-category",
            Produced.with(Serdes.String(), Serdes.Long())
        );

        return stream;
    }
}
```

### Stream with windowed aggregation

```java
@Bean
public void windowedOrderCount(StreamsBuilder builder) {
    KStream<String, OrderEvent> orders = builder.stream("order-events");

    TimeWindowedKStream<String, OrderEvent> windowed = orders
        .groupByKey()
        .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)));

    KTable<Windowed<String>, Long> counts = windowed.count();

    counts.toStream()
        .map((key, value) -> KeyValue.pair(
            key.key() + "@" + key.window().startTime().toString(),
            value
        ))
        .to("order-counts-windowed");
}
```

## Testing

### Embedded Kafka

```java
@SpringBootTest
@EmbeddedKafka(
    partitions = 3,
    topics = {"order-events", "order-events.dlq", "order-events.retry"}
)
class OrderEventPublisherTest {

    @Autowired
    private KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${spring.kafka.bootstrap-servers}")
    private String bootstrapServers;

    @Test
    void shouldPublishOrderCreatedEvent() throws Exception {
        // Given
        OrderCreatedEvent event = new OrderCreatedEvent(1L, 100L, BigDecimal.TEN, Instant.now());

        // When
        kafkaTemplate.send("order-events", "1", event).get();

        // Then verify the consumer received it
        // Use a CountDownLatch or Awaitility
    }
}
```

### Consumer Test with KafkaListenerTestHarness

```java
@SpringBootTest
@EmbeddedKafka(topics = {"order-events"})
class OrderConsumerTest {

    @Autowired
    private KafkaTemplate<String, Object> kafkaTemplate;

    @Test
    void shouldConsumeOrderEvent(@Autowired KafkaListenerEndpointRegistry registry) throws Exception {
        // Send a test event
        OrderCreatedEvent event = new OrderCreatedEvent(1L, 100L, BigDecimal.TEN, Instant.now());
        kafkaTemplate.send("order-events", "1", event).get();

        // Wait for the consumer to process
        await().atMost(10, TimeUnit.SECONDS)
            .untilAsserted(() -> {
                // assert side effects
            });
    }
}
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Send | `KafkaTemplate.send()` | Async — use `.whenComplete()` for callback |
| Consume | `@KafkaListener` | Auto-commits by default; use manual ack for control |
| Retry | `DefaultErrorHandler` + `DeadLetterPublishingRecoverer` | Exponential backoff + DLQ |
| Transactions | `kafkaTemplate.executeInTransaction()` | Requires `transactional.id` + `isolation.level=read_committed` |
| Idempotent producer | `enable.idempotence: true` | Deduplicates retries automatically |
| Streams | `StreamsBuilder` / `KStream` / `KTable` | Requires `spring.kafka.streams.application-id` |
| Windowed aggregation | `TimeWindows.ofSizeWithNoGrace()` | 5-min tumbling windows |
| Testing | `@EmbeddedKafka` | In-memory Kafka for tests |
| Partition key | `ProducerRecord` key | Same key → same partition → ordering guarantee |
| Compression | `compression.type: lz4` | Reduces network I/O; zstd for max ratio |

## Common Pitfalls

1. **Auto-commit in non-idempotent consumers.** If `enable-auto-commit: true` (default) and processing fails after the offset is committed, the message is lost. Use manual ack (`ack-mode: manual_immediate`) for at-least-once processing.

2. **No DLQ strategy.** A poison message that always fails will block the partition indefinitely. Always configure a `DefaultErrorHandler` with `DeadLetterPublishingRecoverer` and a max-retry count.

3. **Blocking inside `@KafkaListener`.** Long-running operations block the consumer thread, preventing progress on other records. Offload heavy work to a separate thread pool or use reactive consumers.

4. **Missing `spring.json.trusted.packages`.** `JsonDeserializer` rejects payloads from untrusted packages by default. Add your package to the trusted list or use a specific type mapping.

5. **Key serializer mismatch.** If the producer uses `StringSerializer` for keys but the consumer uses `IntegerDeserializer`, deserialization fails silently or noisily. Ensure serializers/deserializers match on both sides.

6. **Not using idempotent producers.** Without `enable.idempotence: true`, retried sends can create duplicates. Enable idempotence (default in newer Kafka versions) and set `acks=all`.

7. **Stream state store not persisted.** By default, Kafka Streams state stores are in-memory and lost on restart. Set `state.dir` to a persistent path and use `processing.guarantee: exactly_once_v2` for stateful stream processing.

8. **Ignoring partition ordering.** Ordering is guaranteed per partition, not across partitions. If event ordering matters, use a meaningful partition key (e.g., `orderId`) so related events land on the same partition.

9. **Consumer group rebalances during processing.** If a consumer takes too long, it may be kicked out of the group (session timeout). Increase `max.poll.interval.ms` for batch consumers or process records in smaller batches.

10. **Mixing transactional and non-transactional sends.** A transactional producer cannot send non-transactional records. All sends must be inside `executeInTransaction()` or the producer's transactional context.