# backend-by-hand

Building core backend components by hand, to learn how backend actually works.
No frontend. Python + FastAPI. Tested with curl and Postman. Deployed manually
to an EC2 VM behind nginx and systemd.

| # | Component | What it teaches | Status |
|---|-----------|-----------------|--------|
| 0 | Raw HTTP server | What a request and response actually are, in bytes, with no framework | 🟨 |
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

## Agendas

Each component is worked through one step at a time. Component 0 reflects
actual progress. The agendas for 1 to 12 are drafts and get refined when the
component starts.

### 0. Raw HTTP server

Plain Python `socket`, no framework. Done when one server run answers many
curl GET and POST requests on different paths correctly, with no restart.

1. ✅ Listen on a TCP socket, accept a connection, print the raw request bytes.
2. ✅ Send a hand-built HTTP response with a correct `Content-Length`; set `SO_REUSEADDR` for instant restarts.
3. ✅ Parse the request line and route by path: 200, 404, 400 for a malformed request line, 405 with an `Allow` header.
4. 🟨 Read the full request: `recv()` loop until `\r\n\r\n`, then read `Content-Length` body bytes; handle `recv()` returning `b''`; cap header size (431); add a POST path that uses the body.
5. ⬜ Serve forever and handle multiple clients: `Connection: close`, then threads.
6. ⬜ Optional: compare with `http.server`, then uvicorn and ASGI, as the bridge to component 1.

### 1. CRUD API (in-memory)

1. ⬜ FastAPI hello world under uvicorn; map what it replaces from component 0.
2. ⬜ Path and query parameters; list and fetch items from a Python dict.
3. ⬜ Create, update and delete with the right status codes (201, 204, 404, 409).
4. ⬜ Validate JSON bodies by hand and return clear 400 or 422 errors.
5. ⬜ Replace the hand validation with Pydantic models and compare.
6. ⬜ Share logic through plain function calls, then through `Depends()`.

### 2. Persistence

1. ⬜ `sqlite3` from the stdlib: connect, create a table, insert and select in a script.
2. ⬜ Swap the CRUD dict for SQLite with raw parameterised SQL; try SQL injection against your own code.
3. ⬜ Transactions: commit, rollback, and what a crash mid-write leaves behind.
4. ⬜ Move to Postgres: drivers, connection strings, connection pooling.
5. ⬜ Hand-written migration files, then Alembic.
6. ⬜ Rewrite the same queries with an ORM and read the SQL it emits.

### 3. Auth

1. ⬜ Users table and sign-up with bcrypt; why not plain text or a bare SHA hash.
2. ⬜ Login: verify the hash, give one generic error for a wrong user or password.
3. ⬜ Server-side sessions: session ID cookie, sessions table, logout.
4. ⬜ JWT by hand with `hmac` and `hashlib`, then with a library.
5. ⬜ Expiry, refresh tokens and revocation; sessions versus JWT trade-offs.
6. ⬜ Turn "who is the current user" into a dependency.

### 4. Authorization

1. ⬜ 401 versus 403, and when each applies.
2. ⬜ Ownership checks: users can only change their own resources; 403 versus 404 and what each leaks.
3. ⬜ Roles stored in the database, checked per route.
4. ⬜ Permissions mapped to roles instead of hard-coded role checks.
5. ⬜ Centralise the checks and test every route with curl as each role.

### 5. File uploads

1. ⬜ Capture raw `multipart/form-data` bytes and find the boundaries by reading them.
2. ⬜ FastAPI `UploadFile`: streaming to disk versus holding in memory.
3. ⬜ Size limits (413) and type checks by magic bytes, not extension (415).
4. ⬜ Safe filenames, path traversal, storage location, metadata in the database.
5. ⬜ Download endpoint with correct `Content-Type` and `Content-Disposition`.

### 6. Rate limiting

1. ⬜ Fixed-window counter per IP in memory; 429 with `Retry-After`.
2. ⬜ Token bucket by hand.
3. ⬜ Move the limiter into middleware.
4. ⬜ Why in-memory state breaks with several processes; move the state to Redis.
5. ⬜ Finding the real client IP behind nginx, and when to trust `X-Forwarded-For`.

### 7. Caching

1. ⬜ Measure a slow endpoint; add an in-process cache with a TTL.
2. ⬜ Install Redis and use `redis-cli`: `GET`, `SET`, `EXPIRE`.
3. ⬜ Cache-aside pattern from the API.
4. ⬜ Invalidation on writes and the stale-read problem.
5. ⬜ HTTP caching: `Cache-Control`, `ETag`, 304 Not Modified.

### 8. Background jobs

1. ⬜ Measure how a slow task blocks the response.
2. ⬜ FastAPI `BackgroundTasks` and why it dies with the process.
3. ⬜ Hand-rolled queue: a jobs table in Postgres and a polling worker (`FOR UPDATE SKIP LOCKED`).
4. ⬜ Retries with backoff, a dead-letter state, idempotent jobs.
5. ⬜ A Redis-backed queue library, compared with the hand-rolled one.

### 9. Payments API

1. ⬜ Stripe test mode: keys in environment variables, call the API with curl first.
2. ⬜ Orders table; create a payment from your own API.
3. ⬜ Webhooks: receive them locally, verify the signature by hand, then with the SDK.
4. ⬜ Idempotency keys on your own POST endpoints and on Stripe calls.
5. ⬜ Order state machine; duplicate and out-of-order webhook events.

### 10. Logging & observability

1. ⬜ `print` versus the `logging` module: levels, handlers, formatters.
2. ⬜ Structured JSON logs.
3. ⬜ Request ID middleware, carried into every log line and the response headers.
4. ⬜ Access log: method, path, status, duration.
5. ⬜ Debug a planted bug using only the logs.

### 11. Linux basics

1. ⬜ SSH keys, `~/.ssh/config`, `ssh-agent`.
2. ⬜ Users, groups, `sudo`, `chmod` and `chown`; a dedicated service user.
3. ⬜ Filesystem layout: `/etc`, `/var/log`, `/opt`, `/srv`, home directories.
4. ⬜ `apt`, `PATH`, Python virtual environments on a server.
5. ⬜ Processes, signals and ports: `ps`, `top`, `kill`, `ss -tlnp`.

### 12. Deployment

1. ⬜ Launch an EC2 instance, open ports 22, 80 and 443 in the security group, SSH in.
2. ⬜ Run the app with uvicorn by hand and reach it on the public IP.
3. ⬜ Write a systemd unit file: restart on failure, read logs with `journalctl`.
4. ⬜ Write the nginx reverse proxy config by hand, including proxy headers.
5. ⬜ `ufw`, TLS with certbot, redirect HTTP to HTTPS.
6. ⬜ Ship an update by hand: pull, restart, environment variables and secrets.
