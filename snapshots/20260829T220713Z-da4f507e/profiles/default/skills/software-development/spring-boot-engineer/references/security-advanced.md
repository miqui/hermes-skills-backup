# Advanced Security — OAuth2 Login, Authorization Server, Sessions, SAML & Security Testing

> Reference for: Spring Boot Engineer
> Load when: Implementing OAuth2 social login, Spring Authorization Server, session-based auth, SAML2 SSO, security testing, or multi-tenant security

> **Note:** For JWT filter setup, OAuth2 Resource Server, method security annotations, and `UserDetailsService`, see `references/security.md`. This file covers the advanced topics not in that reference.

## OAuth2 Social Login (Google, GitHub)

### Client Registration

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: profile, email
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope: read:user, user:email
```

### SecurityFilterChain with oauth2Login

```java
@Configuration
@EnableWebSecurity
public class OAuth2LoginSecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login**", "/error", "/webjars/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(login -> login
                .loginPage("/login")
                .successHandler(oAuth2AuthenticationSuccessHandler())
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService())
                )
            )
            .logout(logout -> logout
                .logoutSuccessUrl("/")
                .invalidateHttpSession(true)
                .deleteCookies("JSESSIONID")
            );
        return http.build();
    }

    @Bean
    public AuthenticationSuccessHandler oAuth2AuthenticationSuccessHandler() {
        return (request, response, authentication) -> {
            OAuth2AuthenticationToken oauthToken = (OAuth2AuthenticationToken) authentication;
            OAuth2User oauthUser = oauthToken.getPrincipal();

            // Map OAuth2 user to your domain user
            User user = userService.findOrCreateFromOAuth2(
                oauthToken.getAuthorizedClientRegistrationId(),
                oauthUser.getAttribute("email"),
                oauthUser.getAttribute("name")
            );

            // Issue your own session or JWT
            response.sendRedirect("/dashboard");
        };
    }

    @Bean
    public OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService() {
        return new CustomOAuth2UserService();
    }
}
```

### Custom OAuth2UserService

```java
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService implements OAuth2UserService<OAuth2UserRequest, OAuth2User> {

    private final UserRepository userRepository;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oauth2User = new DefaultOAuth2UserService().loadUser(userRequest);

        String email = oauth2User.getAttribute("email");
        String provider = userRequest.getClientRegistration().getRegistrationId();

        User user = userRepository.findByEmail(email)
            .orElseGet(() -> {
                User newUser = User.builder()
                    .email(email)
                    .authProvider(provider)
                    .active(true)
                    .roles(Set.of(Role.builder().name("USER").build()))
                    .build();
                return userRepository.save(newUser);
            });

        // Add domain roles alongside OAuth2 attributes
        Map<String, Object> attributes = new HashMap<>(oauth2User.getAttributes());
        attributes.put("userId", user.getId());
        attributes.put("roles", user.getRoles().stream()
            .map(r -> "ROLE_" + r.getName())
            .collect(Collectors.toList()));

        return new DefaultOAuth2User(
            user.getRoles().stream()
                .map(r -> new SimpleGrantedAuthority("ROLE_" + r.getName()))
                .collect(Collectors.toSet()),
            attributes,
            "email"
        );
    }
}
```

## Spring Authorization Server (OAuth2 Server Role)

### Dependencies

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-authorization-server</artifactId>
</dependency>
```

### AuthorizationServerConfiguration

```java
@Configuration
@EnableWebSecurity
public class AuthorizationServerConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
        OAuth2AuthorizationServerConfiguration.applyDefaultSecurity(http);

        http.getConfigurer(OAuth2AuthorizationServerConfigurer.class)
            .oidc(Customizer.withDefaults());  // enable OpenID Connect 1.0

        http
            .exceptionHandling(ex -> ex
                .defaultAuthenticationEntryPointFor(
                    new LoginUrlAuthenticationEntryPoint("/login"),
                    new MediaTypeRequestMatcher(MediaType.TEXT_HTML)
                )
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));

        return http.build();
    }

    @Bean
    public RegisteredClientRepository registeredClientRepository() {
        RegisteredClient clientCredentialsClient = RegisteredClient.withId(UUID.randomUUID().toString())
            .clientId("service-client")
            .clientSecret("{noop}service-secret")
            .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
            .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
            .redirectUri("http://127.0.0.1:8080/login/oauth2/code/service-client")
            .scope(OidcScopes.OPENID)
            .scope("client.read")
            .scope("client.write")
            .clientSettings(ClientSettings.builder()
                .requireAuthorizationConsent(true)
                .build())
            .tokenSettings(TokenSettings.builder()
                .accessTokenTimeToLive(Duration.ofMinutes(15))
                .refreshTokenTimeToLive(Duration.ofDays(7))
                .build())
            .build();

        return new InMemoryRegisteredClientRepository(clientCredentialsClient);
    }

    @Bean
    public JWKSource<SecurityContext> jwkSource() {
        RSAKey rsaKey = generateRsaKey();
        JWKSet jwkSet = new JWKSet(rsaKey);
        return (jwkSelector, securityContext) -> jwkSelector.select(jwkSet);
    }

    private static RSAKey generateRsaKey() {
        try {
            KeyPair keyPair = KeyPairGenerator.getInstance("RSA")
                .generateKeyPair();
            return new RSAKey.Builder("key-id")
                .privateKey((RSAPrivateKey) keyPair.getPrivate())
                .publicKey((RSAPublicKey) keyPair.getPublic())
                .keyID(UUID.randomUUID().toString())
                .build();
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    @Bean
    public JwtDecoder jwtDecoder(JWKSource<SecurityContext> jwkSource) {
        return OAuth2AuthorizationServerConfiguration.jwtDecoder(jwkSource);
    }

    @Bean
    public AuthorizationServerSettings authorizationServerSettings() {
        return AuthorizationServerSettings.builder()
            .issuer("https://auth.example.com")
            .build();
    }
}
```

### PKCE Support

```java
@Bean
public RegisteredClient pkceClient() {
    return RegisteredClient.withId(UUID.randomUUID().toString())
        .clientId("spa-client")
        .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)  // public client
        .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
        .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
        .redirectUri("https://spa.example.com/callback")
        .scope(OidcScopes.OPENID)
        .scope("profile")
        .clientSettings(ClientSettings.builder()
            .requireProofKey(true)   // require PKCE
            .build())
        .build();
}
```

## Session-Based Authentication

### Form Login Configuration

```java
@Bean
@Order(2)
public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/login", "/register", "/css/**", "/js/**").permitAll()
            .anyRequest().authenticated()
        )
        .formLogin(form -> form
            .loginPage("/login")
            .loginProcessingUrl("/authenticate")
            .defaultSuccessUrl("/dashboard", true)
            .failureUrl("/login?error=true")
            .permitAll()
        )
        .sessionManagement(session -> session
            .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
            .maximumSessions(1)
            .maxSessionsPreventsLogin(false)  // kick out old session
            .sessionRegistry(sessionRegistry())
        )
        .csrf(csrf -> csrf
            .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
        );
    return http.build();
}
```

### Concurrent Session Control

```java
@Bean
public SessionRegistry sessionRegistry() {
    return new SpringSessionBackedSessionRegistry<>(sessionRepository);
}

@Bean
public HttpSessionEventPublisher httpSessionEventPublisher() {
    return new HttpSessionEventPublisher();
}
```

### Remember-Me

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .formLogin(form -> form.loginPage("/login").permitAll())
        .rememberMe(remember -> remember
            .key("unique-and-secret-key")
            .tokenValiditySeconds(Duration.ofDays(30).toSeconds())
            .rememberMeParameter("remember-me")
        );
    return http.build();
}
```

## SAML2 SSO

### Dependencies

```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-saml2-service-provider</artifactId>
</dependency>
```

### Relying Party Configuration

```yaml
spring:
  security:
    saml2:
      relyingparty:
        registration:
          okta-sp:
            identityprovider:
              entity-id: "http://www.okta.com/EXKGHD"
              metadata-uri: "https://dev.okta.com/app/EXKGHD/sso/saml/metadata"
            assertingparty:
              entity-id: "https://app.example.com/saml2/service-provider-metadata/okta-sp"
              singlesignon:
                sign-request: false
```

### SAML2 Login Flow

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/saml2/**", "/login/**").permitAll()
            .anyRequest().authenticated()
        )
        .saml2Login(saml2 -> saml2
            .loginProcessingUrl("/login/saml2/SSO/{registrationId}")
            .defaultSuccessUrl("/dashboard", true)
        );
    return http.build();
}
```

## Security Testing

### @WithMockUser

```java
@WebMvcTest(UserController.class)
@Import(SecurityConfig.class)
class UserControllerSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser(username = "admin", roles = "ADMIN")
    @DisplayName("Admin can access all users endpoint")
    void adminCanAccessAllUsers() throws Exception {
        mockMvc.perform(get("/api/v1/users"))
            .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(username = "user", roles = "USER")
    @DisplayName("Non-admin gets 403 on all users endpoint")
    void nonAdminGetsForbidden() throws Exception {
        mockMvc.perform(get("/api/v1/users"))
            .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Anonymous gets 401")
    void anonymousGetsUnauthorized() throws Exception {
        mockMvc.perform(get("/api/v1/users"))
            .andExpect(status().isUnauthorized());
    }
}
```

### @WithUserDetails

```java
@Test
@WithUserDetails(value = "admin@example.com", userDetailsServiceBeanName = "customUserDetailsService")
void adminUserCanDelete() throws Exception {
    mockMvc.perform(delete("/api/v1/users/1"))
        .andExpect(status().isNoContent());
}
```

### Custom SecurityContext for Tests

```java
public class WithMockCustomUserSecurityContextFactory
        implements WithSecurityContextFactory<WithMockCustomUser> {

    @Override
    public SecurityContext createSecurityContext(WithMockCustomUser annotation) {
        SecurityContext context = SecurityContextHolder.createEmptyContext();

        Collection<SimpleGrantedAuthority> authorities = List.of(
            new SimpleGrantedAuthority("ROLE_ADMIN")
        );

        Authentication auth = new UsernamePasswordAuthenticationToken(
            annotation.username(),
            "password",
            authorities
        );

        context.setAuthentication(auth);
        return context;
    }
}

@Retention(RetentionPolicy.RUNTIME)
@WithSecurityContext(factory = WithMockCustomUserSecurityContextFactory.class)
public @interface WithMockCustomUser {
    String username() default "admin";
}
```

### CSRF Test Support

```java
@SpringBootTest
@AutoConfigureMockMvc
class CsrfSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser
    void postWithoutCsrfTokenReturns403() throws Exception {
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"test\"}"))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser
    void postWithCsrfTokenSucceeds() throws Exception {
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"test\"}")
                .with(csrf()))
            .andExpect(status().isCreated());
    }
}
```

### OAuth2 Test Utilities

```java
@SpringBootTest
@AutoConfigureMockMvc
class OAuth2ResourceServerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void validJwtReturnsOk() throws Exception {
        Jwt jwt = Jwt.withTokenValue("token")
            .header("alg", "RS256")
            .claim("sub", "user123")
            .claim("scope", "read")
            .build();

        mockMvc.perform(get("/api/v1/users/me")
                .with(jwt().jwt(jwt)))
            .andExpect(status().isOk());
    }

    @Test
    void noTokenReturns401() throws Exception {
        mockMvc.perform(get("/api/v1/users/me"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void insufficientScopeReturns403() throws Exception {
        Jwt jwt = Jwt.withTokenValue("token")
            .header("alg", "RS256")
            .claim("sub", "user123")
            .claim("scope", "read")
            .build();

        mockMvc.perform(get("/api/v1/admin/dashboard")
                .with(jwt().jwt(jwt)))
            .andExpect(status().isForbidden());
    }
}
```

## Multi-Tenancy Security Patterns

### Tenant Resolution Filter

```java
@Component
@RequiredArgsConstructor
@Order(1)
public class TenantResolutionFilter extends OncePerRequestFilter {

    private final TenantService tenantService;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        String tenantId = extractTenantId(request);

        if (tenantId != null) {
            TenantContext.setTenantId(tenantId);
        }

        try {
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }

    private String extractTenantId(HttpServletRequest request) {
        // From header, subdomain, or JWT claim
        String header = request.getHeader("X-Tenant-Id");
        if (header != null) return header;

        // Or from JWT if using OAuth2
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth instanceof JwtAuthenticationToken jwtAuth) {
            return jwtAuth.getToken().getClaim("tenant_id");
        }
        return null;
    }
}
```

### Tenant-Aware Authentication

```java
public class TenantAwareAuthenticationToken extends UsernamePasswordAuthenticationToken {
    private final String tenantId;

    public TenantAwareAuthenticationToken(Object principal, Object credentials,
                                          String tenantId,
                                          Collection<? extends GrantedAuthority> authorities) {
        super(principal, credentials, authorities);
        this.tenantId = tenantId;
    }

    public String getTenantId() { return tenantId; }
}
```

## Security Event Logging & Auditing

```java
@Component
@Slf4j
public class SecurityEventListener {

    @EventListener
    public void onAuthenticationSuccess(AuthenticationSuccessEvent event) {
        log.info("auth_success principal={} ip={} timestamp={}",
            event.getAuthentication().getName(),
            SecurityContextHolder.getContext().getAuthentication(),
            event.getTimestamp()
        );
    }

    @EventListener
    public void onAuthenticationFailure(AbstractAuthenticationFailureEvent event) {
        log.warn("auth_failure principal={} exception={} timestamp={}",
            event.getAuthentication().getName(),
            event.getException().getMessage(),
            event.getTimestamp()
        );
    }

    @EventListener
    public void onAuthorizationDenied(AuthorizationDeniedEvent event) {
        log.warn("authz_denied principal={} authority={}",
            event.getAuthentication().getName(),
            event.getAuthorities()
        );
    }
}
```

```java
@Bean
public ApplicationListener<AuthenticationSuccessEvent> authenticationSuccessListener() {
    return event -> {
        Counter.builder("auth.success")
            .tag("principal", event.getAuthentication().getName())
            .register(meterRegistry)
            .increment();
    };
}
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Social login | `oauth2Login()` | Configure clients in `application.yml` |
| Custom user mapping | `OAuth2UserService` | Map OAuth2 attributes to domain user |
| Authorization Server | `OAuth2AuthorizationServerConfigurer` | Spring Authorization Server project |
| PKCE | `requireProofKey(true)` | For SPA / public clients |
| Form login | `formLogin()` | Session-based, stateful |
| Concurrent sessions | `maximumSessions(1)` | Requires `HttpSessionEventPublisher` |
| Remember-me | `rememberMe()` | Persistent or token-based |
| SAML2 SSO | `saml2Login()` | IdP metadata via `metadata-uri` |
| Security tests | `@WithMockUser`, `@WithUserDetails` | Test-specific authentication |
| CSRF in tests | `.with(csrf())` | MockMvc CSRF token injection |
| OAuth2 tests | `.with(jwt().jwt(jwt))` | Mock JWT for resource server |
| Multi-tenancy | `TenantContext` + filter | ThreadLocal tenant resolution |

## Common Pitfalls

1. **Missing `HttpSessionEventPublisher` for concurrent session control.** Without this bean, Spring Security cannot detect session destruction, and `maximumSessions()` will not work correctly.

2. **Storing OAuth2 client secrets in config files.** Use environment variables or a secrets manager. Never commit `client-secret` to source control.

3. **Not mapping OAuth2 users to domain users.** The `DefaultOAuth2UserService` returns attributes as-is. A custom `OAuth2UserService` is needed to create or link domain users, assign roles, and enforce business rules.

4. **Using `@EnableResourceServer` (deprecated).** Spring Security 6+ removed this annotation. Use `oauth2ResourceServer(jwt -> jwt...)` in the `SecurityFilterChain` instead.

5. **SAML2 metadata URI pointing to local file in prod.** The `metadata-uri` should point to the IdP's metadata endpoint. Using a local file requires manual rotation when the IdP rotates its keys.

6. **Not testing CSRF in stateful apps.** Form-login apps with session management MUST have CSRF protection enabled and tested. The default is on, but custom configurations can accidentally disable it.

7. **Forgetting `@Order` on authorization server filter chain.** The authorization server's `SecurityFilterChain` must have higher priority (lower `@Order` value) than the resource server's chain, or requests to the authorization server endpoints will be handled by the wrong chain.

8. **Using `InMemoryRegisteredClientRepository` in production.** This is fine for development but does not persist across restarts. Use a `JdbcRegisteredClientRepository` or a custom implementation for production.

9. **Not handling `OAuth2AuthenticationException` in the custom `OAuth2UserService`.** If user creation fails (e.g., duplicate email), throw `OAuth2AuthenticationException` to abort the login flow — don't return a partial or null user.

10. **Tenant context leaking across async boundaries.** `TenantContext` using `ThreadLocal` will not propagate to `@Async` methods. Use `TaskDecorator` to copy context, or prefer virtual threads.
