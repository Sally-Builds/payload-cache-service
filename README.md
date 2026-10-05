# Payload Caching Service

A FastAPI microservice that generates payloads from two string lists and caches
aggressively at two levels, plus a CLI tool to exercise it. Built as a coding
assessment; AI tools were used and every line is owned and understood.

## What it does

`POST /payload` accepts two equal-length string lists. Each string is passed
through a "transformer" (a simulated external service), and the service returns
the interleaving of the transformed strings. `GET /payload/{id}` reads a
generated payload back.

Two-level caching keeps external calls to a minimum:

1. **Payload cache** — an identical request returns the already-generated
   payload's identifier; no work happens at all.
2. **Transform cache** — a new request reuses transformed values for every
   input string seen before; only unseen strings hit the transformer, and
   those are transformed concurrently (`asyncio.gather`).

```bash
curl -X POST localhost:8000/payload \
  -H 'Content-Type: application/json' \
  -d '{"list_1": ["first string"], "list_2": ["other string"]}'
# {"id": "1f14feed0584417db8f7aa8fb5a993d6", "message": "Payload generated"}

curl localhost:8000/payload/1f14feed0584417db8f7aa8fb5a993d6
# {"output": "FIRST STRING, OTHER STRING"}
```

## Quickstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The CLI (flags parsed and sanitized with Pydantic Settings):

```bash
./cache-cli --json '{"list_1": ["a"], "list_2": ["b"]}' --repeat 3
echo '{"list_1": ["a"], "list_2": ["b"]}' | ./cache-cli --input - --output out.json
./cache-cli --help
```

`--repeat N` posts the same payload N times and reports per-iteration timing
plus whether all iterations returned the same id, which makes the caching
visible: the first call does the transformer work, repeats are ~instant.

Docker:

```bash
docker compose up --build
```

The SQLite cache lives on a named volume so it survives restarts. For
PostgreSQL instead, set
`CACHE_DATABASE_URL=postgresql+asyncpg://user:pass@host/db`.

Tests:

```bash
.venv/bin/python -m pytest tests/ -q   # 26 tests, unit + integration
```

## Design decisions

- **Async end to end** (async FastAPI endpoints, async SQLModel sessions,
  async transformer) because the workload is I/O-bound; no sync call ever
  blocks the event loop.
- **Cache keys are SHA-256 hashes**: the payload key hashes the canonical JSON
  of both lists (fixed key order, compact separators), so identical requests
  collide by design and anything else does not. Transform keys hash the exact
  raw string, which is what the transformer receives.
- **Dedupe before transforming**: a string repeated inside one request is
  transformed once.
- **Race-safe payload insert**: `input_hash` is unique; on an
  `IntegrityError` from two concurrent identical requests the loser rolls back
  and reuses the winner's id instead of 500ing.
- **SQLite by default, PostgreSQL by URL switch** (both async drivers in
  `requirements.txt`); the task allows either.
- **The transformer is an explicit seam** (`app/transformer.py`): swapping in
  the real external service means replacing one class, and its observable
  `calls` counter lets tests prove call minimization.

## Documented shortcuts and deviations

- The spec assigns `-h` to both `--host` and `--help`. `-h` means help
  (universal convention); `--host` is long-form only.
- pydantic-settings' CLI parser supports long flags only, so the `-r`/`-i`/
  `-j`/`-o` short forms are unavailable; the long forms behave as specified,
  including `-` for stdin/stdout.
- The Docker image could not be built in the sandbox used for development
  (no Docker daemon); the Dockerfile follows the same layout the service was
  run and tested with locally.
- Validation errors return FastAPI's standard 422; unknown ids return 404.

## Time log

Machine build time will be noted in the submission email; the hours reported
there are the author's own honest total, including review and the walkthrough
recording.
