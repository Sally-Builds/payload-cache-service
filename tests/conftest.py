"""Shared test helpers.

Uses a temp-file SQLite database per test so tests never touch the real
cache.db. Also strips proxy env vars: httpx (used by the CLI and starlette's
TestClient) crashes at client construction on the malformed proxy variables
present in some sandboxes/CI environments.
"""

import asyncio
import os

for _var in (
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
):
    os.environ.pop(_var, None)

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


def run(coro):
    """Run an async callable from a sync test (no pytest-asyncio needed)."""
    return asyncio.run(coro)


def make_test_db(tmp_path):
    """Create an isolated SQLite DB; returns (engine, session_factory)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    run(_init())
    return engine, factory
