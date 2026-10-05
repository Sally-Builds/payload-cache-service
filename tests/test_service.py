"""Tests for the two-level caching orchestration.

Uses a counting TransformerClient to prove the core requirement: the number
of external transformer calls is minimized (each distinct string is
transformed at most once, ever).
"""

import pytest
from sqlmodel import select

from app.db import Payload
from app.service import get_or_build_payload
from app.transformer import TransformerClient
from tests.conftest import make_test_db, run


@pytest.fixture()
def db(tmp_path):
    return make_test_db(tmp_path)


def _build(db, list_1, list_2, transformer):
    _, factory = db

    async def _run():
        async with factory() as session:
            return await get_or_build_payload(list_1, list_2, session, transformer)

    return run(_run())


def _read_output(db, payload_id):
    _, factory = db

    async def _run():
        async with factory() as session:
            row = (
                await session.exec(select(Payload).where(Payload.id == payload_id))
            ).first()
            return row.output

    return run(_run())


def test_first_build_transforms_each_unique_string_once(db):
    transformer = TransformerClient(latency_seconds=0)
    payload_id, created = _build(db, ["a", "b"], ["c", "a"], transformer)
    assert created is True
    assert transformer.calls == 3  # "a" appears twice but is transformed once
    assert _read_output(db, payload_id) == "A, C, B, A"


def test_repeat_build_reuses_id_and_makes_no_calls(db):
    transformer = TransformerClient(latency_seconds=0)
    payload_id, _ = _build(db, ["a"], ["b"], transformer)
    assert transformer.calls == 2

    payload_id_2, created_2 = _build(db, ["a"], ["b"], transformer)
    assert created_2 is False
    assert payload_id_2 == payload_id
    assert transformer.calls == 2  # zero new external calls


def test_partial_overlap_only_transforms_new_strings(db):
    transformer = TransformerClient(latency_seconds=0)
    _build(db, ["a"], ["b"], transformer)
    assert transformer.calls == 2

    payload_id, created = _build(db, ["a"], ["c"], transformer)
    assert created is True
    assert transformer.calls == 3  # only "c" was new
    assert _read_output(db, payload_id) == "A, C"


def test_output_matches_spec_sample(db):
    transformer = TransformerClient(latency_seconds=0)
    payload_id, _ = _build(
        db,
        ["first string", "second string", "third string"],
        ["other string", "another string", "last string"],
        transformer,
    )
    assert _read_output(db, payload_id) == (
        "FIRST STRING, OTHER STRING, SECOND STRING, "
        "ANOTHER STRING, THIRD STRING, LAST STRING"
    )
