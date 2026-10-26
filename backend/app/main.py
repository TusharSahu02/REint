from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.services import data_store

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = data_store.init(settings.data_dir)
    logger.info(
        "data loaded: actuals=%d rows, forecasts=%d raw hourly rows",
        len(store.actuals),
        store.forecast_rows_raw,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Wind Forecast Monitor", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal error"})

    return app


app = create_app()
