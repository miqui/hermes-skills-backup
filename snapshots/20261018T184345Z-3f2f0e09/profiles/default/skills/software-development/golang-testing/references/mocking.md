# Mocking and Test Fixtures

## Mocks and Fakes

Prefer small hand-written fakes for simple interfaces. Reach for `testify/mock` or a generated mock when you need call verification; check the generator's own docs for its API.

For a full `testify/mock` example (defining a mock, matchers, call modifiers, verification), see the `golang-stretchr-testify` skill, `references/mock.md`. It is not duplicated here.

## Hand-written Fake

For small interfaces, a fake that records calls is usually clearer than a framework:

```go
// user_service.go
type Database interface {
    GetUser(id string) (*User, error)
    CreateUser(user *User) error
}
type EmailService interface {
    SendWelcomeEmail(to string) error
}

// user_service_test.go (same package)
type fakeDB struct {
    users map[string]*User
    err   error // injected failure
}

func (f *fakeDB) GetUser(id string) (*User, error) {
    if f.err != nil {
        return nil, f.err
    }
    return f.users[id], nil
}

func (f *fakeDB) CreateUser(u *User) error {
    if f.err != nil {
        return f.err
    }
    f.users[u.ID] = u
    return nil
}

type fakeEmail struct{ sent []string }

func (f *fakeEmail) SendWelcomeEmail(to string) error {
    f.sent = append(f.sent, to)
    return nil
}

func TestUserService_CreateUser(t *testing.T) {
    db, mail := &fakeDB{users: map[string]*User{}}, &fakeEmail{}
    svc := NewUserService(db, mail)

    user := &User{ID: "u1", Name: "Test", Email: "test@example.com"}
    if err := svc.CreateUser(user); err != nil {
        t.Fatalf("CreateUser: %v", err)
    }
    if db.users["u1"] != user {
        t.Error("user not stored")
    }
    if len(mail.sent) != 1 || mail.sent[0] != "test@example.com" {
        t.Errorf("sent = %v, want welcome email to test@example.com", mail.sent)
    }
}
```

Snippets in this file omit some imports for brevity (`testing`, plus whatever each snippet obviously uses).

## Test Fixtures

Create reusable test data in a separate package or file. Return fresh values from constructors rather than sharing mutable package-level variables:

```go
package fixtures

import "time"

// Constructors, not package-level pointers: each test gets its own copy, so
// mutations and t.Parallel() cannot leak between tests.
// Qualify User with its package (e.g. model.User) if it lives elsewhere.
func DefaultUser() *User {
    return &User{
        ID:        "user-123",
        Name:      "Jane Doe",
        Email:     "jane@example.com",
        CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
    }
}

func AdminUser() *User {
    u := DefaultUser()
    u.ID, u.Name, u.Email, u.Role = "admin-1", "Admin User", "admin@example.com", "admin"
    return u
}

// NewUser takes the ID and time as parameters so tests stay deterministic.
func NewUser(id, name, email string, createdAt time.Time) *User {
    return &User{ID: id, Name: name, Email: email, CreatedAt: createdAt}
}
```

## Time Mocking

Use `clockwork` to test time-dependent code without `time.Sleep()`. On Go 1.25+ prefer `testing/synctest` (see SKILL.md); use a fake clock when you need an injectable `Clock` interface. The code under test must read time only from the injected clock.

```go
import (
    "context"
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

    // If the scheduler waits on the clock in its own goroutine, first block
    // until it is waiting, or Advance may fire before the timer is registered.
    // (BlockUntilContext is in current clockwork releases; check your version.
    // Skip this if your scheduler is synchronous.)
    ctx, cancel := context.WithTimeout(t.Context(), 5*time.Second)
    defer cancel()
    _ = fakeClock.BlockUntilContext(ctx, 1)

    // Advance fake time
    fakeClock.Advance(2 * time.Hour)

    // If job execution is asynchronous, wait for it (channel/WaitGroup) before asserting.
    is.Equal(0, scheduler.PendingCount())
}
```

Install clockwork:

```bash
go get github.com/jonboulle/clockwork
```
