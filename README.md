# backend-by-hand

Building core backend components by hand, to learn how backend actually works.
No frontend. Python + FastAPI. Tested with curl and Postman. Deployed manually
to an EC2 VM behind nginx and systemd.

| # | Component | What it teaches | Status |
|---|-----------|-----------------|--------|
| 0 | Raw HTTP server | What a request and response actually are, in bytes, with no framework | ⬜ |
| 1 | CRUD API (in-memory) | Routing, HTTP methods, status codes, hand-written validation, then Pydantic | ⬜ |
| 2 | Persistence | Connections, raw SQL (SQLite → Postgres), migrations, then an ORM | ⬜ |
| 3 | Auth | Password hashing, sessions vs JWT, token expiry | ⬜ |
| 4 | Authorization | Roles, permissions, ownership checks | ⬜ |
| 5 | File uploads | Multipart encoding, storage, size and type limits | ⬜ |
| 6 | Rate limiting | Token bucket, middleware | ⬜ |
| 7 | Caching | Redis, TTLs, cache invalidation | ⬜ |
| 8 | Background jobs | Queues, workers, retries | ⬜ |
| 9 | Payments API | Stripe test mode, webhooks, idempotency | ⬜ |
| 10 | Logging & observability | Structured logs, request IDs, reading logs to debug | ⬜ |
| 11 | Linux basics | SSH and keys, users and permissions, filesystem layout, `apt`, processes and ports | ⬜ |
| 12 | Deployment | EC2, systemd unit files, nginx reverse proxy written by hand, security groups and `ufw`, TLS with certbot | ⬜ |

⬜ not started · 🟨 in progress · ✅ done
