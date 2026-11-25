import asyncpg

from schemas import Advertisement


class ModerationPolicyRepository:
    _MIN_IMAGES = {True: 0, False: 1}

    def get_min_images(self, is_verified_seller: bool) -> int:
        return self._MIN_IMAGES[is_verified_seller]


class UserRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def create(
        self, first_name: str, last_name: str,
        is_verified: bool, violations_qty: int,
    ) -> int:
        return await self._connection.fetchval(
            """
            INSERT INTO users (first_name, last_name, is_verified, violations_qty)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            first_name, last_name, is_verified, violations_qty,
        )


class AdvertisementRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def create(
        self, seller_id: int, name: str, description: str,
        category: int, images_qty: int,
    ) -> int:
        return await self._connection.fetchval(
            """
            INSERT INTO advertisements
                (seller_id, name, description, category, images_qty)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            seller_id, name, description, category, images_qty,
        )

    async def get_for_prediction(self, item_id: int) -> Advertisement | None:
        row = await self._connection.fetchrow(
            """
            SELECT a.id AS item_id, a.seller_id, u.is_verified AS is_verified_seller,
                   a.name, a.description, a.category, a.images_qty
            FROM advertisements AS a
            JOIN users AS u ON u.id = a.seller_id
            WHERE a.id = $1
            """,
            item_id,
        )
        return Advertisement(**dict(row)) if row is not None else None
