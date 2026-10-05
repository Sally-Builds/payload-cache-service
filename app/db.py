"""Database layer: SQLModel models plus the async engine and sessions.

Two tables:
    TransformCache  one row per distinct transformer input ever seen
                    (level-2 cache: avoids repeat external calls)
    Payload         one row per distinct payload request ever seen
                    (level-1 cache: reuses the payload identifier)

Fully async (aiosqlite driver for SQLite, asyncpg for PostgreSQL) so the
async endpoints never block the event loop on I/O.
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .settings import settings


class TransformCache(SQLModel, table=True):
    input_hash: str = Field(primary_key=True, max_length=64)
    input_text: str
    transformed: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Payload(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=32)
    input_hash: str = Field(unique=True, index=True, max_length=64)
    output: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


engine = create_async_engine(settings.database_url)
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with SessionFactory() as session:
        yield session
