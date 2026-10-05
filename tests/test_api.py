"""API integration tests through the real FastAPI app."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_session
from tests.conftest import make_test_db


@pytest.fixture()
def client(tmp_path):
    _, factory = make_test_db(tmp_path)

    async def _override():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE = {
    "list_1": ["first string", "second string", "third string"],
    "list_2": ["other string", "another string", "last string"],
}
SAMPLE_OUTPUT = (
    "FIRST STRING, OTHER STRING, SECOND STRING, "
    "ANOTHER STRING, THIRD STRING, LAST STRING"
)


def test_create_and_read_roundtrip(client):
    created = client.post("/payload", json=SAMPLE)
    assert created.status_code == 201
    payload_id = created.json()["id"]
    assert created.json()["message"]

    read = client.get(f"/payload/{payload_id}")
    assert read.status_code == 200
    assert read.json() == {"output": SAMPLE_OUTPUT}


def test_repeat_post_reuses_identifier(client):
    first = client.post("/payload", json=SAMPLE).json()["id"]
    second = client.post("/payload", json=SAMPLE).json()["id"]
    assert first == second


def test_create_message_reports_transform_cache_usage(client):
    fresh = client.post("/payload", json={"list_1": ["a"], "list_2": ["b"]})
    assert fresh.json()["message"] == (
        "Payload generated: 2 strings transformed, 0 reused from cache"
    )

    partial = client.post("/payload", json={"list_1": ["a"], "list_2": ["c"]})
    assert partial.json()["message"] == (
        "Payload generated: 1 string transformed, 1 reused from cache"
    )

    repeat = client.post("/payload", json={"list_1": ["a"], "list_2": ["c"]})
    assert repeat.json()["message"] == (
        "Payload already existed; reusing existing identifier"
    )


def test_mismatched_lengths_are_rejected(client):
    resp = client.post("/payload", json={"list_1": ["a", "b"], "list_2": ["c"]})
    assert resp.status_code == 422


def test_unknown_id_returns_404(client):
    assert client.get("/payload/does-not-exist").status_code == 404
