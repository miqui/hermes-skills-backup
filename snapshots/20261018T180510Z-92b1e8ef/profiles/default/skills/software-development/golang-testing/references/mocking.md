# Mocking and Test Fixtures

## Mocks and Fakes

Prefer small hand-written fakes for simple interfaces. Reach for `testify/mock` or a generated mock when you need call verification; check the generator's own docs for its API.

The full `testify/mock` example (defining a mock, matchers, call modifiers, verification) lives in the local `golang-stretchr-testify` skill, `references/mock.md`; it is not duplicated here.

Snippets below omit imports (`testing`, `assert`, `mock`) for brevity.

## Mock Organization

For larger codebases, organize mocks alongside the code they mock:

```go
// user_service.go
type UserService struct {
    db    Database
    email EmailService
}
type Database interface {
    GetUser(id string) (*User, error)
    CreateUser(user *User) error
}
type EmailService interface {
    SendWelcomeEmail(to string) error
}
```

```go
// user_service_test.go
package mypackage_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "path/to/mypackage"
)

// MockDatabase implements mypackage.Database
type MockDatabase struct {
    mock.Mock
}
func (m *MockDatabase) GetUser(id string) (*mypackage.User, error) {
    args := m.Called(id)
    if args.Get(0) == nil { return nil, args.Error(1) }
    return args.Get(0).(*mypackage.User), args.Error(1)
}
func (m *MockDatabase) CreateUser(user *mypackage.User) error {
    return m.Called(user).Error(0)
}

// MockEmailService implements mypackage.EmailService
type MockEmailService struct {
    mock.Mock
}
func (m *MockEmailService) SendWelcomeEmail(to string) error {
    return m.Called(to).Error(0)
}

func TestUserService_CreateUser(t *testing.T) {
    mockDB := new(MockDatabase)
    mockEmail := new(MockEmailService)
    service := mypackage.NewUserService(mockDB, mockEmail)

    user := &mypackage.User{Name: "Test", Email: "test@example.com"}
    mockDB.On("CreateUser", user).Return(nil)
    mockEmail.On("SendWelcomeEmail", "test@example.com").Return(nil)

    err := service.CreateUser(user)

    assert.NoError(t, err)
    mockDB.AssertExpectations(t)
    mockEmail.AssertExpectations(t)
}
```

## Test Fixtures

Create reusable test data in a separate package or file:

```go
package fixtures

import "time"

var (
    DefaultUser = &User{
        ID:        "user-123",
        Name:      "Jane Doe",
        Email:     "jane@example.com",
        CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
    }

    AdminUser = &User{
        ID:        "admin-1",
        Name:      "Admin User",
        Email:     "admin@example.com",
        Role:      "admin",
        CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
    }
)

// NewUser takes the ID and time as parameters so tests stay deterministic.
func NewUser(id, name, email string, createdAt time.Time) *User {
    return &User{ID: id, Name: name, Email: email, CreatedAt: createdAt}
}
```

## Time Mocking

Use `clockwork` to test time-dependent code without `time.Sleep()`. On Go 1.25+ prefer `testing/synctest` (see SKILL.md); use a fake clock when you need an injectable `Clock` interface. The code under test must read time only from the injected clock.

```go
import (
    "testing"
    "time"
    "github.com/jonboulle/clockwork"
    "github.com/stretchr/testify/assert"
)

func TestScheduler_AddJob(t *testing.T) {
    is := assert.New(t)

    fakeClock := clockwork.NewFakeClock()
    scheduler := NewScheduler(fakeClock)

    job := &Job{ID: "1", RunAt: fakeClock.Now().Add(time.Hour)}
    scheduler.AddJob(job)

    is.Equal(1, scheduler.PendingCount())

    // Advance fake time
    fakeClock.Advance(2 * time.Hour)

    is.Equal(0, scheduler.PendingCount())
}
```

Install clockwork:

```bash
go get github.com/jonboulle/clockwork
```
