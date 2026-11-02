# Runtime and Protocols

## Runtime contract

AgentCore Runtime hosts an agent or tool endpoint. Before implementation, verify the current Runtime contract in the official AWS documentation for the chosen protocol, region, image architecture, health check, request path, authentication, and streaming requirements. These details can change independently of the application framework.

The supplied source uses these starting points; validate them rather than assuming they are service invariants:

| Protocol | Intended use | Source-template starting point |
|---|---|---|
| HTTP | Custom application API | `/invocations`, `/ping`, port 8080 |
| MCP | Tools, resources, prompts exposed to an MCP client | streamable HTTP `/mcp`, port 8000 |
| A2A | Agent-to-agent collaboration | root endpoint and agent card, port 9000 |
| AG-UI | Agent-to-frontend events | `/invocations` event stream, `/ping`, port 8080 |

A single configured Runtime should use one protocol. Make protocol selection before generating container, framework, and authentication configuration.

## Protocol selection

- **HTTP**: Use when your caller owns the request schema and you need a conventional app API. Document request/response schemas, streaming semantics, auth, and error handling.
- **MCP**: Use when the primary product is reusable agent tooling. Keep tools small, typed, observable, authorization-aware, and safe against prompt-derived arguments.
- **A2A**: Use for agent interoperability, capability discovery, and delegated tasks. Publish only accurate agent-card capabilities.
- **AG-UI**: Use when a frontend needs a standardized agent event stream. Ensure event encoding, cancellation, reconnection, and user/session state are explicit.

## Container checklist

1. Build an ARM64-compatible image when the current Runtime environment requires it.
2. Use a multi-stage build, pinned base image digest where feasible, and locked dependencies.
3. Run as a non-root user and include no development secrets or credential files.
4. Bind to the protocol-required interface/port and expose a health endpoint if required.
5. Validate startup, health endpoint, and representative request locally before publishing an image.
6. Scan the image and review generated SBOM/vulnerability findings before deployment.

See `templates/Dockerfile.runtime-template` and the protocol templates only as examples.

## Sessions and persistence

Do not assume an in-memory session map is durable or portable. Choose deliberately:

- **AgentCore Memory** for managed short-/long-term agent memory and cross-session retrieval where service semantics fit.
- **S3 Files or another durable store** for artifacts and explicit application state.
- **External databases** for transactional or queryable business state.
- **In-process session state** only for short-lived, non-critical affinity patterns with a clear recovery story.

Validate tenant isolation, retention/deletion, encryption, and recovery behavior for every persisted data path.

## MCP and tool lifecycle

For an HTTP Runtime that calls an MCP server, create and close the client through application lifecycle hooks. Keep server URLs configurable, restrict outbound destinations, and treat all tool results as untrusted external data. An MCP client-side tool allowlist is useful exposure control, not an authorization boundary; enforce privileged decisions at the MCP server, proxy/Gateway, or downstream backend.

## Framework notes

The source package includes FastAPI, FastMCP, Strands, AG-UI, and A2A examples. Confirm installed library compatibility from current project lockfiles and vendor docs before use. Do not copy source defaults for model IDs, regions, or package extras into production without review.
