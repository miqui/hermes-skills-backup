# GraalVM Native Image — AOT Compilation & Deployment

> Reference for: Spring Boot Engineer
> Load when: Building, configuring, or troubleshooting GraalVM native images with Spring Boot 3.x

## Overview

Spring Boot 3.x ships with a built-in Ahead-of-Time (AOT) engine that transforms the application at build time, enabling GraalVM Native Image compilation. The AOT engine resolves bean definitions, computes Spring configuration, and generates native hints at build time, eliminating runtime reflection and bytecode generation where possible.

Native images produced by GraalVM are ahead-of-time compiled binaries that offer:
- Fast startup (milliseconds, not seconds)
- Low memory footprint
- Container-native deployment without a JVM

**Trade-off:** Native images cannot use runtime bytecode generation (CGLIB proxies), dynamic class loading, or late binding. All reflection, resources, and serialization must be declared at build time via hints.

## Dependencies

### Maven

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
    </dependency>
    <!-- graalvm metadata reachability repository for third-party libs -->
    <dependency>
        <groupId>org.graalvm.nativeimage</groupId>
        <artifactId>svm</artifactId>
        <scope>provided</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.graalvm.buildtools</groupId>
            <artifactId>native-maven-plugin</artifactId>
        </plugin>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>
```

### Gradle (Kotlin DSL)

```kotlin
plugins {
    id("org.springframework.boot")
    id("io.spring.dependency-management")
    id("org.graalvm.buildtools.native") version "0.10.2"
    java
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter")
}
```

## Build Commands

### Maven

```bash
# Generate AOT sources (Spring AOT processing)
./mvnw native:compile-no-fork

# Full native image build (AOT + native compile)
./mvnw -Pnative native:compile

# Build a native image using buildpacks (Docker)
./mvnw spring-boot:build-image -Pnative -Dspring-boot.build-image.image-name=app:native
```

### Gradle

```kotlin
// build.gradle.kts
tasks.named<org.springframework.boot.gradle.tasks.bundling.BootJar>("bootJar") {
    layered {
        enabled = true
    }
}

// Native compile task
tasks.named<org.graalvm.buildtools.gradle.tasks.NativeBuildTask>("nativeCompile") {
    // options configured automatically by Spring Boot plugin
}
```

```bash
# Gradle native build
./gradlew nativeCompile

# Test native image
./gradlew nativeTest
```

### Buildpacks (Pack CLI)

```bash
# No local GraalVM installation required
pack build app:native \
    --builder paketobuildpacks/builder:tiny \
    --env BP_NATIVE_IMAGE=true \
    --path target/
```

## AOT Processing

Spring Boot's AOT engine runs during the build and performs:

1. **Bean definition resolution** — all `@Bean` methods are resolved to concrete instances
2. **Configuration property binding** — bindings are pre-computed
3. **Reflection hints generation** — needed classes, methods, and fields are registered
4. **Resource hints** — files that need to be available at runtime are registered

```yaml
spring:
  aot:
    enabled: true   # typically set by the build plugin, not manually
```

### Inspecting AOT output

```bash
# AOT-generated sources are under target/spring-aot/main/
ls target/spring-aot/main/java/
# AOT-generated resources are under target/spring-aot/main/resources/
ls target/spring-aot/main/resources/META-INF/native-image/
```

## Runtime Hints API

When third-party libraries or application code require runtime reflection, resources, or serialization that the AOT engine cannot detect, register explicit hints.

### RuntimeHintsRegistrar

```java
public class CustomHintsRegistrar implements RuntimeHintsRegistrar {

    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Register reflection for a specific class
        hints.reflection().registerType(MyDto.class,
            MemberCategory.DECLARED_FIELDS,
            MemberCategory.INVOKE_PUBLIC_METHODS
        );

        // Register resources (files on classpath)
        hints.resources().registerPattern("schema/*.xsd");
        hints.resources().registerPattern("templates/*.html");

        // Register serialization for Jackson
        hints.serialization().registerType(MySerializable.class);

        // Register dynamic proxies
        hints.proxies().registerJdkProxy(MyInterface.class);
    }
}
```

```java
@Configuration
@ImportRuntimeHints(CustomHintsRegistrar.class)
public class NativeConfig {
}
```

### MemberCategory options

```java
// Available categories for reflection hints
MemberCategory.INVOKE_PUBLIC_METHODS
MemberCategory.INVOKE_DECLARED_METHODS
MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS
MemberCategory.INVOKE_DECLARED_CONSTRUCTORS
MemberCategory.PUBLIC_FIELDS
MemberCategory.DECLARED_FIELDS
MemberCategory.PUBLIC_CLASSES
MemberCategory.DECLARED_CLASSES
```

### Conditional hints

```java
public class ConditionalHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Only register if the class is present on the classpath
        if (ClassUtils.isPresent("com.example.OptionalLib", classLoader)) {
            hints.reflection().registerType(
                ClassUtils.resolveClassName("com.example.OptionalLib", classLoader),
                MemberCategory.INVOKE_PUBLIC_METHODS
            );
        }
    }
}
```

## Known Limitations & Gotchas

### No CGLIB proxies

GraalVM Native Image cannot generate CGLIB proxies at runtime. Spring Boot's AOT engine detects `@Configuration` classes and marks them for proxy-based interception at build time, but:

- **`@Configuration(proxyBeanMethods = false)`** is recommended to avoid proxy generation entirely
- Custom proxy-based solutions (e.g., `ProxyFactoryBean`) may not work without explicit hints

### JPA / Hibernate

- Hibernate's bytecode enhancement (lazy loading) uses runtime proxies that may not survive native compilation
- Use `hibernate.use_sql_comments=true` for debugging, not bytecode enhancement
- Register reflection hints for entity classes if lazy loading is needed
- Consider using DTO projections to avoid lazy-loading proxies entirely

```java
// Register entity hints for native
public class JpaEntityHintsRegistrar implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        for (Class<?> entity : List.of(User.class, Order.class, Product.class)) {
            hints.reflection().registerType(entity,
                MemberCategory.DECLARED_FIELDS,
                MemberCategory.INVOKE_PUBLIC_METHODS
            );
        }
    }
}
```

### Third-party library support

- Use the GraalVM reachability metadata repository: `https://github.com/oracle/graalvm-reachability-metadata`
- Many common libraries (Jackson, Logback, HikariCP) are already supported by Spring Boot's built-in hints
- For unsupported libraries, add `RuntimeHintsRegistrar` or `@RegisterReflectionForBinding` annotations

### Spring profiles

- `spring.profiles.active` must be set at build time or via `native-args.txt`
- Dynamic profile activation at runtime is limited; prefer build-time configuration

### Classpath scanning

- Runtime classpath scanning (e.g., `@ComponentScan` with packages) is resolved at build time by the AOT engine
- Dynamic classpath scanning at runtime will NOT work unless explicit hints are registered
- Use `@Import` or `@ComponentScan` with explicit package names — the AOT engine handles them at build time

### Logging

- Logback configuration (`logback-spring.xml`) is supported, but some features require hints
- Logback `<include>` of external files may need resource hints
- JUL (java.util.logging) is the fallback on native image; configure it explicitly if needed

## Testing Native Images

### NativeTestConfiguration

```java
@TestConfiguration
@ImportRuntimeHints(MyTestHints.class)
public class NativeTestConfig {
    // Register hints needed only for tests
}
```

### Running native tests

```bash
# Maven — compile and run native tests
./mvnw -Pnative test

# Gradle
./gradlew nativeTest
```

### JVM vs native tests

- Run tests on the JVM first for fast feedback
- Run native tests as a CI gate before deployment
- Native test compilation is slow (minutes); use it as a verification step, not for development

## Docker Build

### Multi-stage Dockerfile (native)

```dockerfile
# Build stage — uses GraalVM
FROM ghcr.io/graalvm/native-image-community:21 AS builder
WORKDIR /build

# Copy Maven wrapper and pom
COPY mvnw .
COPY .mvn .mvn
COPY pom.xml .
COPY src src

# Build native image
RUN ./mvnw -Pnative -DskipTests native:compile

# Runtime stage — minimal image
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 libz1 && rm -rf /var/lib/apt/lists/*

COPY --from=build /build/target/native-native-image-test /app/app

EXPOSE 8080
ENTRYPOINT ["/app/app"]
```

### Buildpacks (simpler)

```bash
# Using Spring Boot buildpacks (no local GraalVM needed)
./mvnw spring-boot:build-image \
    -Pnative \
    -Dspring-boot.build-image.image-name=app:native \
    -Dspring-boot.build-image.env.BP_NATIVE_IMAGE=true
```

## Quick Reference

| Concern | API / Command | Notes |
|---|---|---|
| Build (Maven) | `./mvnw -Pnative native:compile` | Requires GraalVM installed |
| Build (Gradle) | `./gradlew nativeCompile` | Requires GraalVM installed |
| Build (Docker) | `pack build ... -e BP_NATIVE_IMAGE=true` | No local GraalVM needed |
| AOT output | `target/spring-aot/main/` | Inspect generated sources |
| Reflection hints | `RuntimeHintsRegistrar` | Register in `@Configuration` |
| Serialization hints | `hints.serialization().registerType()` | For Jackson, etc. |
| Resource hints | `hints.resources().registerPattern()` | Classpath files |
| Proxy hints | `hints.proxies().registerJdkProxy()` | JDK dynamic proxies |
| Conditional hints | `ClassUtils.isPresent()` check | Avoid startup failures |
| Entity hints | `MemberCategory.DECLARED_FIELDS` | For JPA entities |

## Common Pitfalls

1. **Forgetting `@Configuration(proxyBeanMethods = false)`.** CGLIB proxy generation is not supported at runtime. This annotation avoids proxy generation and is the recommended default for native images.

2. **Hibernate lazy loading without hints.** Lazy-loading proxies use bytecode generation that fails in native images. Register reflection hints for entity classes or use DTO projections to avoid proxies entirely.

3. **Third-party libraries without reachability metadata.** Libraries not covered by Spring Boot's built-in hints or the GraalVM metadata repository will fail at runtime with `ClassNotFoundException` or `NoSuchMethodException`. Register `RuntimeHintsRegistrar` for them.

4. **Runtime classpath scanning.** Dynamic `@ComponentScan` with broad patterns is resolved at build time, but runtime scanning (e.g., custom `ClassPathScanningCandidateComponentProvider`) will not find classes unless hints are registered.

5. **Dynamic Spring profiles.** Setting `spring.profiles.active` at runtime via environment variables works, but dynamic profile activation via `spring.config.import` or `Environment` post-processing is limited.

6. **Large native image build time.** Native compilation can take several minutes. Use JVM mode for development and native compilation only in CI or release builds.

7. **Not testing the native image.** Tests passing on the JVM do not guarantee the native image works. Run `nativeTest` as a CI gate to catch reflection and resource issues early.

8. **Missing resource hints for classpath files.** Files loaded via `getResourceAsStream()` or `@Value("classpath:...")` need explicit resource hints. The AOT engine cannot detect all dynamic resource access patterns.

9. **Assuming JNI or native libraries work.** JNI calls require native library configuration via `--initialize-at-build-time` and `--link-at-build-time` flags. Not all native libraries are compatible with GraalVM.

10. **Using `@PostConstruct` for native-incompatible initialization.** `@PostConstruct` methods that rely on runtime reflection or dynamic class loading will fail. Move such logic to build-time configuration or register appropriate hints.
