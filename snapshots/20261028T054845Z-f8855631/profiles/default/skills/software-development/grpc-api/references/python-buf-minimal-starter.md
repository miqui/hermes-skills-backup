# Python + Buf minimal starter

Use this reference when creating a small greenfield Python gRPC repo with Buf-managed code generation.

## Recommended layout

```text
project/
  proto/
    <scope>/hello/v1/hello.proto
  src/
    <app_pkg>/
      server.py
      client.py
    <scope>/hello/v1/
      hello_pb2.py
      hello_pb2_grpc.py
  buf.yaml
  buf.gen.yaml
  pyproject.toml
```

## Naming pitfall: avoid `grpc.*` as your proto package root

For Python targets, do **not** use a proto package/path rooted at `grpc`, such as:

```proto
package grpc.api.hello.v1;
```

Why:
- Python generated imports will live under `grpc/...`
- that collides with the runtime `grpc` package from `grpcio`
- application imports like `from grpc.api.hello.v1 import ...` become ambiguous or broken

Prefer a project-owned scope instead, for example:

```proto
package bufexample.hello.v1;
```

or a real org/domain-owned scope.

## Minimal contract

```proto
syntax = "proto3";

package bufexample.hello.v1;

service HelloService {
  rpc SayHello(SayHelloRequest) returns (SayHelloResponse);
}

message SayHelloRequest {
  string name = 1;
}

message SayHelloResponse {
  string message = 1;
}
```

## Minimal Buf config

`buf.yaml`

```yaml
version: v2
modules:
  - path: proto
lint:
  use:
    - STANDARD
breaking:
  use:
    - FILE
```

`buf.gen.yaml`

```yaml
version: v2
managed:
  enabled: false
plugins:
  - remote: buf.build/protocolbuffers/python
    out: src
  - remote: buf.build/grpc/python
    out: src
```

## Python deps

A minimal `pyproject.toml` runtime usually only needs:

- `grpcio`
- `protobuf`

Add `pytest` for a smoke round-trip test.

## Packaging pitfall: `uv sync` alone is not enough without a build backend

If the repo uses a `src/` layout, include a `[build-system]` table in `pyproject.toml`. Without it, `uv sync` installs dependencies but does **not** install the project itself, so `src/` never gets added to `sys.path` through an editable install.

That usually shows up as import failures for your application package or generated stubs, for example `ModuleNotFoundError: grpc_api_buf_example` even though the files exist under `src/`.

A safe minimal pattern is:

```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"
```

With a build backend present, `uv sync` can install the project in editable mode, which makes both the app package and Buf-generated modules under `src/` importable.

## Verification flow

1. `buf lint`
2. `buf generate`
3. run a tiny server/client round trip
4. run pytest against the round-trip smoke test

## Compatibility notes

- Keep a version suffix in the proto package from day one, such as `v1`
- Never reuse field numbers
- Reserve deleted fields when evolving the contract
- Keep the initial example unary unless streaming is actually required
