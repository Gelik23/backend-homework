from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from routers.predict import router, validation_error
from routers.simple_predict import router as simple_predict_router

app = FastAPI(title="Модерация объявлений")
app.add_exception_handler(RequestValidationError, validation_error)
app.include_router(router)
app.include_router(simple_predict_router)
