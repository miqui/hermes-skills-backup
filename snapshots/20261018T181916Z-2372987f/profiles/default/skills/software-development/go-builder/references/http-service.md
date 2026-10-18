# Production HTTP Service Defaults

Stdlib-only sketch (Go 1.22+ `ServeMux` patterns, which need a `go` line of 1.22+ in `go.mod`; `log/slog`, graceful shutdown).

```go
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	if err := run(); err != nil {
		slog.Error("server failed", "err", err)
		os.Exit(1)
	}
}

func run() error {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{"id": r.PathValue("id")})
	})

	srv := &http.Server{
		Addr:              ":" + envOr("PORT", "8080"),
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second, // mitigates slowloris; never leave unset
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() { errCh <- srv.ListenAndServe() }()
	logger.Info("listening", "addr", srv.Addr)

	select {
	case err := <-errCh:
		if !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			return err
		}
		logger.Info("shutdown complete")
	}
	return nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
```

Notes:

- Tune `WriteTimeout` to your slowest legitimate response; streaming endpoints should use `http.ResponseController` deadlines instead.
- Bound request bodies with `http.MaxBytesReader(w, r.Body, limit)`.
- `slog` key-value args must alternate key, value; the `sloglint` linter enforces consistency.
- Keep the shutdown timeout below the orchestrator's termination grace period.

## Dockerfile (multi-stage, distroless)

```dockerfile
ARG GO_VERSION=1.24 # set to the go version in go.mod or current stable
FROM golang:${GO_VERSION} AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server

FROM gcr.io/distroless/static-debian13:nonroot
COPY --from=build /out/server /server
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/server"]
```

- Use a builder tag at least as new as the `go` line in `go.mod`, and the current Debian tag for the distroless base.
- `CGO_ENABLED=0` is required for the `static` base image; use a `base` image if you need cgo.
- Add a `.dockerignore` excluding `.git`, `bin/`, `.env`, and test artifacts.
- Distroless has no shell or curl; run health checks from the orchestrator against `/healthz`.
