# Advanced Data Access — NoSQL, Caching & Modern Error Responses

> Reference for: Spring Boot Engineer
> Load when: Using Spring Data MongoDB/Redis, Spring Cache abstraction, Caffeine, or RFC 9457 Problem Details

## Spring Data MongoDB

### Configuration

```java
@Configuration
@EnableMongoRepositories(basePackages = "com.example.app.repository.mongo")
public class MongoConfig {

    @Bean
    public MongoClient mongoClient() {
        return MongoClients.create("mongodb://localhost:27017");
    }

    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(mongoClient(), "appdb");
    }
}
```

```yaml
# application.yml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/appdb
      # For clustered/replica-set deployments:
      # uri: mongodb://host1:27017,host2:27017,host3:27017/appdb?replicaSet=rs0
```

### Document and Repository

```java
@Document(collection = "products")
@CompoundIndex(name = "sku_tenant_idx", def = "{'sku': 1, 'tenantId': 1}", unique = true)
@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Product {
    @Id
    private String id;

    @Indexed
    private String sku;

    @Field("tenant_id")
    private String tenantId;

    @NotBlank
    private String name;

    private BigDecimal price;

    @Version
    private Long version;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
```

```java
public interface ProductRepository extends MongoRepository<Product, String> {

    Optional<Product> findBySkuAndTenantId(String sku, String tenantId);

    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    @Query("{ 'category': ?0, 'active': true }")
    Page<Product> findActiveByCategory(String category, Pageable pageable);

    // Full-text search
    @Query("{ '$text': { '$search': ?0 } }")
    List<Product> fullTextSearch(String term);
}
```

### MongoDB Auditing

```java
@Configuration
@EnableMongoAuditing
public class MongoAuditingConfig {
}
```

### Aggregation Pipeline

```java
@Service
@RequiredArgsConstructor
public class ProductAnalyticsService {

    private final MongoTemplate mongoTemplate;

    public List<CategoryRevenue> revenueByCategory() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.group("category")
                .sum(ConvertToPrice.toBigDecimal("price")).as("totalRevenue")
                .count().as("productCount"),
            Aggregation.sort(Sort.by(Direction.DESC, "totalRevenue"))
        );

        AggregationResults<CategoryRevenue> results =
            mongoTemplate.aggregate(aggregation, "products", CategoryRevenue.class);

        return results.getMappedResults();
    }
}

public record CategoryRevenue(String category, BigDecimal totalRevenue, long productCount) {}
```

## Spring Data Redis

### Configuration

```java
@Configuration
@EnableRedisRepositories(basePackages = "com.example.app.repository.redis")
public class RedisConfig {

    @Bean
    public LettuceConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        return new LettuceConnectionFactory(config);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory());
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());
        return template;
    }
}
```

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      # Sentinel:
      # sentinel:
      #   master: mymaster
      #   nodes: host1:26379,host2:26379,host3:26379
      # Cluster:
      # cluster:
      #   nodes: host1:6379,host2:6379,host3:6379
```

### Redis Entity and Repository

```java
@RedisHash("sessions")
@TimeToLive(unit = TimeUnit.SECONDS)
public class UserSession {
    @Id
    private String id;
    private String userId;
    private String tenantId;
    private Instant lastAccessedAt;

    @Indexed
    private String userId;  // enables findByUserId
}
```

```java
public interface SessionRepository extends CrudRepository<UserSession, String> {
    List<UserSession> findByUserId(String userId);
}
```

### RedisTemplate Operations

```java
@Service
@RequiredArgsConstructor
public class CacheService {
    private final RedisTemplate<String, Object> redisTemplate;

    public void cacheRateLimit(String userId, int remaining, Duration ttl) {
        redisTemplate.opsForValue().set(
            "rate_limit:" + userId,
            remaining,
            ttl
        );
    }

    public boolean acquireLock(String key, Duration ttl) {
        String lockKey = "lock:" + key;
        Boolean acquired = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "locked", ttl);
        return Boolean.TRUE.equals(acquired);
    }

    public void releaseLock(String key) {
        redisTemplate.delete("lock:" + key);
    }
}
```

## Spring Cache Abstraction

### Enable Caching

```java
@Configuration
@EnableCaching
public class CacheConfig {
    // Bean definitions for cache manager are auto-configured when providers are on the classpath.
}
```

### Declarative Caching with Annotations

```java
@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    @Cacheable(value = "products", key = "#id")
    public ProductResponse findById(Long id) {
        return productRepository.findById(id)
            .map(ProductResponse::from)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found"));
    }

    @Cacheable(value = "products", key = "#sku", unless = "#result == null")
    public ProductResponse findBySku(String sku) {
        return productRepository.findBySku(sku)
            .map(ProductResponse::from)
            .orElse(null);
    }

    @CachePut(value = "products", key = "#result.id")
    public ProductResponse update(Long id, ProductUpdateRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found"));
        product.setName(request.name());
        product.setPrice(request.price());
        return ProductResponse.from(productRepository.save(product));
    }

    @CacheEvict(value = "products", key = "#id")
    public void delete(Long id) {
        productRepository.deleteById(id);
    }

    @CacheEvict(value = "products", allEntries = true)
    public void evictAllCache() {
        log.info("All product cache entries evicted");
    }
}
```

### Caffeine (In-Process) Cache Manager

```java
@Bean
public CaffeineCacheManager cacheManager() {
    CaffeineCacheManager cacheManager = new CaffeineCacheManager();
    cacheManager.setCaffeine(Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofMinutes(10))
        .maximumSize(1_000)
        .recordStats());  // enables CacheStats MBean
    return cacheManager;
}
```

### Redis Cache Manager

```java
@Bean
public CacheManager cacheManager(RedisConnectionFactory factory) {
    RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
        .entryTtl(Duration.ofMinutes(15))
        .disableCachingNullValues()
        .serializeKeysWith(
            RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer())
        )
        .serializeValuesWith(
            RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer())
        );

    Map<String, RedisCacheConfiguration> perCacheConfig = Map.of(
        "products", config.entryTtl(Duration.ofMinutes(30)),
        "sessions", config.entryTtl(Duration.ofMinutes(5)),
        "rateLimits", config.entryTtl(Duration.ofSeconds(10))
    );

    return RedisCacheManager.builder(factory)
        .cacheDefaults(config)
        .withInitialCacheConfigurations(perCacheConfig)
        .transactionAware()
        .build();
}
```

```yaml
spring:
  cache:
    type: redis
    redis:
      time-to-live: 15m
      cache-names: products, sessions, rateLimits
```

### Cache Pitfalls

- **Cache penetration**: Querying non-existent keys hits the database each time. Cache `null` or use a Bloom filter for known-absent keys (set `cacheNullValues=true` and use `unless` in `@Cacheable`).
- **Cache avalanche**: Many entries expire simultaneously. Use jittered TTLs or a stale-while-revalidate pattern.
- **Cache stampede**: Hot key expiry triggers multiple cache misses. Use a lock or `@Cacheable(sync = true)` to synchronize cache loads.
- **Serialization mismatch**: `RedisTemplate` and `@Cacheable` serializers must agree — a Jackson-serialized value from `RedisTemplate` cannot be deserialized by the cache infrastructure's serializer without matching configuration.

## Multi-Store Coexistence (JPA + MongoDB + Redis)

```java
// Layer repository interfaces by store — keep domain boundaries clear
@Service
@RequiredArgsConstructor
@Transactional
public class OrderService {
    private final OrderRepository orderRepository;        // JPA — transactional writes
    private final ProductRepository productRepository;    // MongoDB — catalog reads
    private final SessionRepository sessionRepository;    // Redis — ephemeral state

    public Order createOrder(OrderRequest request, String sessionId) {
        UserSession session = sessionRepository.findById(sessionId)
            .orElseThrow(() -> new SessionExpiredException("Session expired"));

        Product product = productRepository.findBySkuAndTenantId(
            request.sku(), session.getTenantId()
        ).orElseThrow(() -> new ResourceNotFoundException("Product not found"));

        Order order = Order.builder()
            .userId(session.getUserId())
            .sku(product.getSku())
            .amount(product.getPrice())
            .status(OrderStatus.PENDING)
            .build();

        return orderRepository.save(order);  // JPA transaction
    }
}
```

## RFC 9457 Problem Details (Spring 6)

Spring Framework 6.0+ ships native `ProblemDetail` support. Prefer it over custom error DTOs for new REST APIs.

### Enable Custom Problem Details

```java
@RestControllerAdvice
public class ProblemDetailExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage()
        );
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://api.example.com/errors/resource-not-found"));
        problem.setInstance(URI.create(request.getRequestURI()));

        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("resourceType", ex.getResourceType());
        problem.setProperty("resourceId", ex.getResourceId());

        return problem;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Validation failed"
        );
        problem.setTitle("Validation Error");

        Map<String, String> fieldErrors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                fe -> fe.getDefaultMessage() != null ? fe.getDefaultMessage() : "Invalid"
            ));

        problem.setProperty("errors", fieldErrors);
        return problem;
    }
}
```

### Global ProblemDetail Configuration

```yaml
spring:
  mvc:
    problemdetails:
      enabled: true
```

### Response Shape

```json
{
  "type": "https://api.example.com/errors/resource-not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Product with sku 'ABC-123' not found",
  "instance": "/api/v1/products/ABC-123",
  "timestamp": "2026-08-18T14:23:01.482Z",
  "resourceType": "Product",
  "resourceId": "ABC-123"
}
```

## Quick Reference

| Concern | Primary annotation/API | Notes |
|---|---|---|
| MongoDB document | `@Document`, `@Id`, `@Indexed` | Auditing via `@EnableMongoAuditing` |
| Redis hash | `@RedisHash`, `@Id`, `@TimeToLive` | Auto-expires entries |
| Cache read | `@Cacheable` | Use `unless` to skip nulls; `sync=true` for stampede protection |
| Cache update | `@CachePut` | Never blocks the method |
| Cache evict | `@CacheEvict` | `allEntries=true` for bulk evict |
| In-process cache | Caffeine | `recordStats()` for Micrometer |
| Distributed cache | Redis | Per-cache TTL via `RedisCacheManager` |
| Error response | `ProblemDetail` | Spring 6+ native RFC 9457 |

## Common Pitfalls

1. **Mixing `@Transactional` with MongoDB.** MongoDB is not an XA/JTA resource. A `@Transactional` method spanning JPA + MongoDB will not roll back the MongoDB write if the JPA insert fails. Keep them in separate methods or accept eventual consistency explicitly.

2. **Forgetting `@Indexed` on MongoDB fields used in queries.** Without an index, queries scan the entire collection.

3. **Cache key collisions.** `@Cacheable(value = "products", key = "#id")` and `@Cacheable(value = "users", key = "#id")` use separate cache namespaces — but a custom key with a generic format can collide across caches.

4. **Caching without TTL.** A cache without an expiry policy can serve stale data indefinitely.

5. **Storing large objects in Redis.** Values are serialized and sent over the network; storing multi-MB payloads can saturate the connection pool.

6. **Not using `ProblemDetail` on Spring 6+.** Custom `ErrorResponse` records duplicate the RFC 9457 structure that Spring now provides natively.

7. **Assuming `@Cacheable` works across service boundaries.** Self-invocation (`this.findById(id)`) bypasses the proxy and skips the cache. Call through the bean or extract to a separate component.

8. **Not locking on cache stampede.** When a hot key expires, N concurrent requests all miss and hit the database. Use `@Cacheable(sync = true)` or a distributed lock.
