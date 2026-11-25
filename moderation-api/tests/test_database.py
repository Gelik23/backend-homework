from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import database

pytestmark = pytest.mark.anyio


async def test_connection_closed(monkeypatch):
    connection = AsyncMock()
    monkeypatch.setattr(database.asyncpg, "connect", AsyncMock(return_value=connection))
    dependency = database.get_connection()
    assert await anext(dependency) is connection
    await dependency.aclose()
    connection.close.assert_awaited_once()


async def test_connection_closed_after_failure(monkeypatch):
    connection = AsyncMock()
    monkeypatch.setattr(database.asyncpg, "connect", AsyncMock(return_value=connection))
    dependency = database.get_connection()
    await anext(dependency)
    with pytest.raises(RuntimeError):
        await dependency.athrow(RuntimeError("Service failure"))
    connection.close.assert_awaited_once()


async def test_connection_failure(monkeypatch):
    monkeypatch.setattr(database.asyncpg, "connect", AsyncMock(side_effect=OSError("Private connection details")))
    with pytest.raises(HTTPException) as exc:
        await anext(database.get_connection())
    assert exc.value.status_code == 500
    assert exc.value.detail == "Internal server error"
