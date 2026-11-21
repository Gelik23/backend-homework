import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from repository import ModerationPolicyRepository
from schemas import Advertisement
from service import ModerationService

router = APIRouter()
logger = logging.getLogger(__name__)
moderation_service = ModerationService(ModerationPolicyRepository())


async def validation_error(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": errors})


@router.post(
    "/predict",
    response_model=bool,
    responses={400: {}, "4XX": {}, 500: {}},
)
def predict(advertisement: Advertisement) -> bool:
    try:
        return moderation_service.predict_violation(advertisement)
    except Exception as exc:
        logger.exception(
            "Ошибка при предсказании для объявления %s", advertisement.item_id
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
