"""FastAPI application.

    POST /payload      create (or reuse) a payload, returns its identifier
    GET  /payload/{id} read a generated payload by its identifier
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .db import Payload, get_session, init_db
from .service import get_or_build_payload
from .settings import settings
from .transformer import TransformerClient


class PayloadRequest(BaseModel):
    list_1: list[str] = Field(default_factory=list)
    list_2: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _same_length(self):
        if len(self.list_1) != len(self.list_2):
            raise ValueError("list_1 and list_2 must contain the same number of strings")
        return self


transformer = TransformerClient(latency_seconds=settings.transformer_latency_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Payload Caching Service", lifespan=lifespan)


@app.post("/payload", status_code=201)
async def create_payload(
    body: PayloadRequest, session: AsyncSession = Depends(get_session)
):
    payload_id, created = await get_or_build_payload(
        body.list_1, body.list_2, session, transformer
    )
    return {
        "id": payload_id,
        "message": (
            "Payload generated"
            if created
            else "Payload already existed; reusing existing identifier"
        ),
    }


@app.get("/payload/{payload_id}")
async def read_payload(payload_id: str, session: AsyncSession = Depends(get_session)):
    row = (
        await session.exec(select(Payload).where(Payload.id == payload_id))
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Payload not found")
    return {"output": row.output}
