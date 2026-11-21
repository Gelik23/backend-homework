from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from routers.predict import router, validation_error

app = FastAPI(title="Модерация объявлений")
app.add_exception_handler(RequestValidationError, validation_error)
app.include_router(router)
