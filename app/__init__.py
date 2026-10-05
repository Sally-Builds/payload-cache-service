"""Payload caching service: FastAPI microservice + CLI.

Layout:
    app/settings.py     service configuration (env vars, CACHE_ prefix)
    app/transformer.py  simulated external transformer service
    app/logic.py        pure payload logic: hashing, interleaving, formatting
    app/db.py           SQLModel models, async engine and sessions
    app/service.py      orchestration with two-level caching
    app/main.py         FastAPI application (POST /payload, GET /payload/{id})
    cli.py              cache-cli command line tool (pydantic-settings CliApp)
"""
