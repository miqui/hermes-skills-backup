# Spring Batch — Jobs, Steps, Readers, Writers & Scheduling

> Reference for: Spring Boot Engineer
> Load when: Building batch jobs, configuring readers/writers, partitioning, scheduling, or testing batch pipelines

## Dependencies

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-batch</artifactId>
</dependency>

<!-- For database-backed job repository -->
<dependency>
    <groupId>org.springframework.batch</groupId>
    <artifactId>spring-batch-core</artifactId>
</dependency>
```

```yaml
spring:
  batch:
    jdbc:
      initialize-schema: always   # creates BATCH_* tables
    job:
      enabled: false              # don't auto-run jobs on startup
```

## Job Structure

### Basic Job with Chunk-oriented Step

```java
@Configuration
@RequiredArgsConstructor
public class OrderBatchConfig {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;

    @Bean
    public Job importOrdersJob(Step importOrdersStep) {
        return new JobBuilder("importOrders", jobRepository)
            .incrementer(new RunIdIncrementer())
            .start(importOrdersStep)
            .listener(orderJobListener())
            .build();
    }

    @Bean
    public Step importOrdersStep(
            ItemReader<OrderCsv> reader,
            ItemProcessor<OrderCsv, Order> processor,
            ItemWriter<Order> writer
    ) {
        return new StepBuilder("importOrdersStep", jobRepository)
            .<OrderCsv, Order>chunk(100, transactionManager)
            .reader(reader)
            .processor(processor)
            .writer(writer)
            .faultTolerant()
            .retryLimit(3)
            .retry(TransientException.class)
            .skipLimit(10)
            .skip(InvalidOrderException.class)
            .listener(chunkListener())
            .build();
    }
}
```

### Job Listener

```java
@Bean
public JobExecutionListener orderJobListener() {
    return new JobExecutionListener() {
        @Override
        public void beforeJob(JobExecution jobExecution) {
            log.info("job_started name={} params={}",
                jobExecution.getJobInstance().getJobName(),
                jobExecution.getJobParameters());
        }

        @Override
        public void afterJob(JobExecution jobExecution) {
            BatchStatus status = jobExecution.getStatus();
            log.info("job_finished name={} status={} duration={}ms",
                jobExecution.getJobInstance().getJobName(),
                status,
                jobExecution.getEndTime().getTime() - jobExecution.getStartTime().getTime());
        }
    };
}
```

## Item Readers

### Flat File (CSV)

```java
@Bean
public FlatFileItemReader<OrderCsv> orderCsvReader() {
    return new FlatFileItemReaderBuilder<OrderCsv>()
        .name("orderCsvReader")
        .resource(new FileSystemResource("data/orders.csv"))
        .delimited()
        .delimiter(",")
        .names("orderId", "customerId", "sku", "quantity", "amount", "status")
        .fieldSetMapper(fieldSet -> new OrderCsv(
            fieldSet.readString("orderId"),
            fieldSet.readLong("customerId"),
            fieldSet.readString("sku"),
            fieldSet.readInt("quantity"),
            fieldSet.readBigDecimal("amount"),
            fieldSet.readString("status")
        ))
        .linesToSkip(1)  // skip header
        .strict(true)     // fail if file missing
        .build();
}
```

### JPA Paging Reader

```java
@Bean
public JpaPagingItemReader<Order> pendingOrdersReader(
        EntityManagerFactory entityManagerFactory) {
    return new JpaPagingItemReaderBuilder<Order>()
        .name("pendingOrdersReader")
        .entityManagerFactory(entityManagerFactory)
        .queryString("SELECT o FROM Order o WHERE o.status = 'PENDING' ORDER BY o.id")
        .pageSize(100)
        .build();
}
```

### JDBC Reader

```java
@Bean
public JdbcCursorItemReader<Customer> customerReader(DataSource dataSource) {
    return new JdbcCursorItemReaderBuilder<Customer>()
        .name("customerReader")
        .dataSource(dataSource)
        .sql("SELECT id, email, name, status FROM customers WHERE active = true")
        .rowMapper((rs, rowNum) -> new Customer(
            rs.getLong("id"),
            rs.getString("email"),
            rs.getString("name"),
            rs.getString("status")
        ))
        .fetchSize(100)
        .build();
}
```

## Item Processors

### Simple Transformation

```java
@Bean
public ItemProcessor<OrderCsv, Order> orderProcessor() {
    return csv -> {
        if (csv.quantity() <= 0) {
            throw new InvalidOrderException("Quantity must be positive: " + csv.orderId());
        }
        return Order.builder()
            .orderId(csv.orderId())
            .customerId(csv.customerId())
            .sku(csv.sku())
            .quantity(csv.quantity())
            .amount(csv.amount())
            .status(OrderStatus.valueOf(csv.status().toUpperCase()))
            .importedAt(Instant.now())
            .build();
    };
}
```

### Filtering (return null to skip)

```java
@Bean
public ItemProcessor<Order, Order> activeOrderFilter() {
    return order -> order.getStatus() == OrderStatus.ACTIVE ? order : null;
}
```

## Item Writers

### JPA Writer

```java
@Bean
public JpaItemWriter<Order> orderWriter(EntityManagerFactory emf) {
    JpaItemWriter<Order> writer = new JpaItemWriter<>();
    writer.setEntityManagerFactory(emf);
    return writer;
}
```

### JDBC Writer

```java
@Bean
public JdbcBatchItemWriter<Order> orderJdbcWriter(DataSource dataSource) {
    return new JdbcBatchItemWriterBuilder<Order>()
        .dataSource(dataSource)
        .sql("""
            INSERT INTO orders (order_id, customer_id, sku, quantity, amount, status, imported_at)
            VALUES (:orderId, :customerId, :sku, :quantity, :amount, :status, :importedAt)
            ON CONFLICT (order_id) DO NOTHING
            """)
        .beanMapped()
        .build();
}
```

### Composite Writer (fan-out)

```java
@Bean
public CompositeItemWriter<Order> compositeOrderWriter(
        JpaItemWriter<Order> dbWriter,
        KafkaItemWriter<Order> kafkaWriter) {
    CompositeItemWriter<Order> writer = new CompositeItemWriter<>();
    writer.setDelegates(List.of(dbWriter, kafkaWriter));
    return writer;
}
```

## Tasklet (Single-Task Step)

```java
@Bean
public Step cleanupStep() {
    return new StepBuilder("cleanupStep", jobRepository)
        .tasklet((contribution, chunkContext) -> {
            log.info("cleanup tasklet executing");
            // Perform cleanup, file moves, notifications, etc.
            return RepeatStatus.FINISHED;
        }, transactionManager)
        .build();
}
```

## Multi-Step Job with Flow

```java
@Bean
public Job multiStepJob(Step importStep, Step validateStep, Step cleanupStep) {
    return new JobBuilder("multiStepJob", jobRepository)
        .incrementer(new RunIdIncrementer())
        .start(importStep)
        .on("FAILED").to(cleanupStep)
        .from(importStep).on("*").to(validateStep)
        .from(validateStep).on("*").to(cleanupStep)
        .end()
        .build();
}
```

## Partitioning for Parallel Processing

```java
@Bean
public Job partitionedJob(Step partitionedStep) {
    return new JobBuilder("partitionedImportJob", jobRepository)
        .start(partitionedStep)
        .build();
}

@Bean
public Step partitionedStep(Step slaveStep, JobRepository jobRepository) {
    return new StepBuilder("partitionedStep", jobRepository)
        .partitioner("slaveStep", partitioner())
        .step(slaveStep)
        .gridSize(4)   // 4 partitions
        .taskExecutor(taskExecutor())
        .build();
}

@Bean
public Partitioner partitioner() {
    return gridSize -> {
        Map<String, ExecutionContext> partitions = new HashMap<>();
        for (int i = 0; i < gridSize; i++) {
            ExecutionContext ctx = new ExecutionContext();
            ctx.putInt("partitionIndex", i);
            ctx.putString("inputFile", "data/orders-part-" + i + ".csv");
            partitions.put("partition-" + i, ctx);
        }
        return partitions;
    };
}

@Bean
public TaskExecutor taskExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(4);
    executor.setMaxPoolSize(8);
    executor.setQueueCapacity(25);
    executor.setThreadNamePrefix("batch-");
    return executor;
}
```

## Scheduling

### @Scheduled trigger

```java
@Component
@RequiredArgsConstructor
public class BatchJobScheduler {

    private final JobLauncher jobLauncher;
    private final Job importOrdersJob;

    @Scheduled(cron = "0 0 2 * * *")  // daily at 2 AM
    public void runImportJob() throws Exception {
        JobParameters params = new JobParametersBuilder()
            .addLong("run.id", System.currentTimeMillis())
            .addString("input.file", "data/orders-" +
                LocalDate.now().minusDays(1) + ".csv")
            .toJobParameters();

        log.info("launching job=importOrders params={}", params);
        jobLauncher.run(importOrdersJob, params);
    }
}
```

### Quartz-based scheduling (for cluster-safe triggers)

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
```

## Testing

### JobLauncherTestUtils

```java
@SpringBootTest
class ImportOrdersJobTest {

    @Autowired
    private JobLauncherTestUtils jobLauncherTestUtils;

    @Test
    void shouldImportOrdersSuccessfully() throws Exception {
        JobExecution execution = jobLauncherTestUtils.launchJob(
            new JobParametersBuilder()
                .addString("input.file", "data/test-orders.csv")
                .addLong("run.id", 1L)
                .toJobParameters()
        );

        assertThat(execution.getStatus()).isEqualTo(BatchStatus.COMPLETED);
        assertThat(execution.getStepExecutions())
            .extracting(StepExecution::getWriteCount)
            .containsExactly(100);  // expected row count
    }

    @Test
    void shouldSkipInvalidOrders() throws Exception {
        JobExecution execution = jobLauncherTestUtils.launchStep(
            "importOrdersStep",
            new JobParameters()
        );

        assertThat(execution.getSkipCount()).isEqualTo(2);
    }
}
```

### Test with Testcontainers

```java
@SpringBootTest
@Testcontainers
class BatchJobIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Test
    void shouldReadFromDbAndWriteToDb() throws Exception {
        // Insert test data, run job, verify output
    }
}
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Job | `JobBuilder` | Named pipeline of steps |
| Chunk step | `<I, O>chunk(size)` | Reader → Processor → Writer in batches |
| Tasklet | `tasklet()` | Single task (cleanup, file ops) |
| CSV reader | `FlatFileItemReaderBuilder` | Delimited or fixed-width |
| DB reader | `JpaPagingItemReader` | Pagination for large datasets |
| JPA writer | `JpaItemWriter` | Uses EntityManager |
| JDBC writer | `JdbcBatchItemWriter` | Bulk insert |
| Retry | `.retry(TransientException.class)` | Configurable retry limit |
| Skip | `.skip(InvalidException.class)` | Skip bad records up to limit |
| Partitioning | `.partitioner().gridSize(N)` | Parallel step execution |
| Scheduling | `@Scheduled` or Quartz | Quartz for cluster-safe scheduling |
| Testing | `JobLauncherTestUtils` | Launch jobs/steps in tests |

## Common Pitfalls

1. **Auto-running jobs on startup.** `spring.batch.job.enabled=true` (default) runs all jobs when the application starts. Set to `false` and launch explicitly via a scheduler or API.

2. **Chunk size too large.** A chunk size of 10,000 may cause memory pressure and long transactions. Start with 100–500 and tune based on throughput and memory.

3. **No skip/retry strategy.** A single bad record aborts the entire job without skip or retry configured. Use `.skipLimit().skip()` for expected bad data and `.retryLimit().retry()` for transient failures.

4. **Reading the entire table into memory.** `JpaPagingItemReader` paginates, but a plain `JpaCursorItemReader` or `JdbcTemplate` query without pagination loads all rows. Always use paging for large datasets.

5. **Not using `RunIdIncrementer`.** Without unique job parameters, re-running the same job with the same parameters fails (Spring Batch prevents duplicate job instances). Add `RunIdIncrementer` or a unique timestamp parameter.

6. **Single-threaded by default.** A chunk-oriented step processes records sequentially. Use partitioning or a `TaskExecutor` to parallelize across threads.

7. **Losing job state on restart.** Spring Batch persists job state in `BATCH_*` tables. If the tables are missing or the schema is not initialized, restarts start from scratch. Ensure `spring.batch.jdbc.initialize-schema=always` (or `embedded` for H2).

8. **Flat file encoding issues.** `FlatFileItemReader` defaults to platform encoding. Set `.encoding("UTF-8")` explicitly for files that may contain non-ASCII characters.

9. **Not testing skip/retry behavior.** Tests that only verify the happy path miss skip count, retry behavior, and DLQ interaction. Always test with at least one bad record.

10. **Quartz vs `@Scheduled` in clusters.** `@Scheduled` runs on every node, causing duplicate job launches in a clustered deployment. Use Quartz with a JDBC job store for cluster-safe single-execution scheduling.