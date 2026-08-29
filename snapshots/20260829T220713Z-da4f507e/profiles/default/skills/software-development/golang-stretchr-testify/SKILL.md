---
name: golang-stretchr-testify
description: "Use when writing or reviewing Go tests that rely on stretchr/testify, especially for choosing between assert and require, defining mocks, verifying expectations, organizing suites, and using advanced assertion helpers correctly."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, testify, assertions, mocks, testing]
    related_skills: [golang-testing, golang-lint, golang-troubleshooting]
---

# stretchr/testify

## Overview

`stretchr/testify` complements Go's `testing` package with readable assertions, mock helpers, and test-suite utilities. It should make tests easier to read and failures easier to interpret, not replace the standard `testing` package or encourage overly magical tests.

This skill is for cases where the work is specifically about Testify usage: deciding between `assert` and `require`, structuring `testify/mock` expectations, or organizing stateful suites without making tests brittle.

## When to Use

- Writing Go tests that use `assert`, `require`, `mock`, or `suite`
- Reviewing Testify usage for clarity or correctness
- Choosing how to model mocks and expectation verification
- Refactoring tests that overuse `assert` or misuse `require`
- Debugging confusing Testify failures or weak mock expectations

Do not use this as the primary skill for general Go testing strategy when the task is broader than Testify itself; use `golang-testing` for the wider testing playbook.

## assert vs require

Both packages offer nearly identical assertions. The real difference is failure behavior:

- **assert** records a failure and continues
- **require** stops the test immediately with `FailNow()`

Use `require` for preconditions and setup checks. Use `assert` for value verification after the test can safely continue.

```go
func TestParseConfig(t *testing.T) {
    is := assert.New(t)
    must := require.New(t)

    cfg, err := ParseConfig("testdata/valid.yaml")
    must.NoError(err)
    must.NotNil(cfg)

    is.Equal("production", cfg.Environment)
    is.Equal(8080, cfg.Port)
    is.True(cfg.TLS.Enabled)
}
```

A simple rule: **`require` for guards, `assert` for checks**.

## Core Assertions

```go
is := assert.New(t)

is.Equal(expected, actual)
is.NotEqual(unexpected, actual)
is.EqualValues(expected, actual)
is.EqualExportedValues(expected, actual)

is.Nil(obj)
is.NotNil(obj)
is.True(cond)
is.False(cond)
is.Empty(collection)
is.NotEmpty(collection)
is.Len(collection, n)

is.Contains("hello world", "world")
is.Contains([]int{1, 2, 3}, 2)
is.Contains(map[string]int{"a": 1}, "a")

is.Greater(actual, threshold)
is.Less(actual, ceiling)
is.Positive(val)
is.Negative(val)
is.Zero(val)

is.Error(err)
is.NoError(err)
is.ErrorIs(err, ErrNotFound)
is.ErrorAs(err, &target)
is.ErrorContains(err, "not found")

is.IsType(&User{}, obj)
is.Implements((*io.Reader)(nil), obj)
```

**Argument order matters:** always `(expected, actual)` when the assertion expects both.

## Advanced Assertions

```go
is.ElementsMatch([]string{"b", "a", "c"}, result)
is.InDelta(3.14, computedPi, 0.01)
is.JSONEq(`{"name":"alice"}`, `{"name": "alice"}`)
is.WithinDuration(expected, actual, 5*time.Second)
is.Regexp(`^user-[a-f0-9]+$`, userID)

is.Eventually(func() bool {
    status, _ := client.GetJobStatus(jobID)
    return status == "completed"
}, 5*time.Second, 100*time.Millisecond)

is.EventuallyWithT(func(c *assert.CollectT) {
    resp, err := client.GetOrder(orderID)
    assert.NoError(c, err)
    assert.Equal(c, "shipped", resp.Status)
}, 10*time.Second, 500*time.Millisecond)
```

Use advanced assertions when they make the expectation clearer, not just because they exist.

## testify/mock

Mock interfaces to isolate the unit under test. Embed `mock.Mock`, implement methods with `m.Called()`, and always verify expectations explicitly.

Key helpers include:

- `mock.Anything`
- `mock.AnythingOfType("T")`
- `mock.MatchedBy(func)`
- `.Once()`, `.Times(n)`, `.Maybe()`, `.Run(func)`

For defining mocks, argument matchers, return sequences, and verification patterns, see [Mock reference](./references/mock.md).

## testify/suite

Suites can help when related tests share structured setup and teardown, but they should not hide too much state.

### Lifecycle

```text
SetupSuite()     -> once before all tests
  SetupTest()    -> before each test
    TestXxx()
  TearDownTest() -> after each test
TearDownSuite()  -> once after all tests
```

### Example

```go
type TokenServiceSuite struct {
    suite.Suite
    store   *MockTokenStore
    service *TokenService
}

func (s *TokenServiceSuite) SetupTest() {
    s.store = new(MockTokenStore)
    s.service = NewTokenService(s.store)
}

func (s *TokenServiceSuite) TestGenerate_ReturnsValidToken() {
    s.store.On("Save", mock.Anything, mock.Anything).Return(nil)
    token, err := s.service.Generate("user-42")
    s.NoError(err)
    s.NotEmpty(token)
    s.store.AssertExpectations(s.T())
}

func TestTokenServiceSuite(t *testing.T) {
    suite.Run(t, new(TokenServiceSuite))
}
```

Suite methods such as `s.Equal()` behave like `assert`. For `require` semantics inside suites, use `s.Require()`.

## Common Mistakes

- Forgetting `AssertExpectations(t)` so mocks never prove they were exercised as intended
- Using `Equal` for wrapped errors instead of `ErrorIs`
- Swapping `(expected, actual)` and making diffs misleading
- Using `assert` where a failed precondition should stop the test immediately
- Overusing suites for tests that would be clearer as plain table-driven functions
- Writing mocks that verify implementation details rather than the contract that matters

## Linting

`testifylint` can catch wrong argument order, misuse of assert/require, and other common Testify problems. Use the local `golang-lint` skill for lint policy and configuration.

## Cross-References

- Use `golang-testing` for general test structure, table-driven patterns, CI, integration tests, and broader test-suite design
- Use `golang-troubleshooting` when Testify-based tests are failing for unclear runtime reasons or concurrency issues
- Use `golang-lint` when you need `testifylint` or wider lint enforcement

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The skill clearly separates general Go testing from Testify-specific guidance
- [ ] The assert/require distinction is explicit and consistent
- [ ] Cross-references point only to local skills
- [ ] The mock reference still aligns with the main skill guidance
