import logging
from collections.abc import AsyncIterator

import asyncpg
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    try:
        connection = await asyncpg.connect(
            host="localhost", port=5435, database="hw",
            user="postgres", password="postgres",
        )
    except (OSError, asyncpg.PostgresError) as exc:
        logger.exception("Ошибка подключения к PostgreSQL")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    try:
        yield connection
    finally:
        await connection.close()
