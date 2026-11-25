import logging
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BeforeValidator

from database import get_connection
from repository import AdvertisementRepository
from routers.predict import moderation_service
from service import AdvertisementNotFoundError, SimplePredictionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/simple_predict", response_model=bool,
    responses={400: {}, 404: {}, "4XX": {}, 500: {}},
)
async def simple_predict(
    item_id: Annotated[int, BeforeValidator(int), Query(gt=0, le=2147483647)],
    connection: Annotated[asyncpg.Connection, Depends(get_connection)],
) -> bool:
    service = SimplePredictionService(
        AdvertisementRepository(connection), moderation_service,
    )
    try:
        return await service.predict_violation(item_id)
    except AdvertisementNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Advertisement not found") from exc
    except Exception as exc:
        logger.exception("Ошибка при предсказании для объявления %s", item_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
