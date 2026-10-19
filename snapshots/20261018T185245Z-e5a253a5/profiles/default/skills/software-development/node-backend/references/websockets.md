# WebSockets Reference

## When to Reach for WebSockets

Use WebSockets when the server needs to push events to connected clients in near real time: live dashboards, chat, presence, collaborative editing, notifications, or streaming status updates. Prefer ordinary HTTP when request-response is enough; WebSockets add connection lifecycle, backpressure, auth refresh, and scale concerns.

## Core Patterns

### Separate transport from domain logic

- socket handlers translate events into service calls
- services own business rules
- broadcasting and room membership stay behind a thin gateway layer
- persistence and queue work stay outside the socket transport layer

### Define event contracts clearly

Treat socket events like an API surface. Name events predictably, validate payloads at the boundary, and version breaking changes intentionally.

```ts
socket.on('message:create', async (payload) => {
  const input = messageSchema.parse(payload);
  const message = await messageService.create(input, socket.data.user);
  io.to(input.roomId).emit('message:created', message);
});
```

## Auth and Connection State

Authenticate at connection time and re-check authorization where room or resource access matters. Store minimal typed user/session context on the socket.

Be careful with:
- long-lived stale auth state
- reconnect flows after token expiration
- assuming a connected socket is authorized for every room forever

## Rooms, Presence, and Broadcasting

Use rooms or channels deliberately:
- one room per conversation/resource when fan-out matters
- explicit join/leave logic
- presence derived from connection lifecycle, not just optimistic client state

Avoid broadcasting globally when targeted rooms will do.

## Reliability and Scale

Plan for:
- reconnects and duplicate delivery
- heartbeat/ping timeouts
- idempotent event handling where possible
- horizontal scaling via adapters/pub-sub when multiple instances are involved

## Validation and Rate Limiting

Validate every inbound event. Add rate limits or per-event safeguards for chatty or abuse-prone channels.

## Observability

Track connection count, join/leave churn, event throughput, error rates, and slow handlers. Correlate socket activity with request/user identifiers when privacy-safe.

## Testing

Test:
- successful connection and auth
- unauthorized connection or room join attempts
- event validation failures
- room-targeted broadcasts
- reconnect/idempotency-sensitive flows

## Common Pitfalls

1. Putting business logic directly in socket callbacks.
2. Trusting client-emitted room/user state without server checks.
3. Broadcasting too widely instead of targeting rooms.
4. Ignoring reconnect and duplicate-event behavior.
5. Skipping metrics and visibility into connection churn.

## Checklist

- [ ] Event payloads are validated at the boundary
- [ ] Auth and authorization are checked deliberately
- [ ] Room membership and broadcasts are explicit
- [ ] Reconnect and duplicate-delivery behavior are accounted for
- [ ] Socket traffic is observable through logs/metrics
