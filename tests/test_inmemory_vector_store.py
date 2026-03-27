"""InMemoryVectorStore.get_by_ids contract."""

import pytest

from tests.mocks import InMemoryVectorStore


@pytest.mark.asyncio
async def test_get_by_ids_preserves_requested_order() -> None:
    store = InMemoryVectorStore()
    await store.add_documents(
        ["a", "b"],
        [[0.0] * 8, [0.0] * 8],
        [
            {"source_key": "s", "chunk_id": "0"},
            {"source_key": "s", "chunk_id": "1"},
        ],
    )
    rows = await store.get_by_ids(["s_1", "s_0"])
    assert [r["id"] for r in rows] == ["s_1", "s_0"]
    assert rows[0]["content"] == "b"


@pytest.mark.asyncio
async def test_get_by_ids_omits_unknown_ids() -> None:
    store = InMemoryVectorStore()
    await store.add_documents(["x"], [[0.0] * 8], [{"source_key": "s", "chunk_id": "0"}])
    rows = await store.get_by_ids(["s_0", "missing"])
    assert len(rows) == 1
    assert rows[0]["id"] == "s_0"
