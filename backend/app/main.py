from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.equipment_management import router as equipment_management_router
from app.api.v1.equipment_diagnosis import router as equipment_diagnosis_router
from app.api.v1.manufacturing import router as manufacturing_router
from app.api.v1.manufacturing_reports import router as manufacturing_reports_router
from app.api.v1.manufacturing_predictions import router as manufacturing_predictions_router
from app.api.v1.data_chat import router as data_chat_router
from app.core.config import get_settings
from app.db.session import create_database_tables


def create_app(create_tables: bool = True) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if create_tables:
            create_database_tables()
        yield

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(datasets_router)
    app.include_router(audit_logs_router)
    app.include_router(manufacturing_router)
    app.include_router(equipment_management_router)
    app.include_router(equipment_diagnosis_router)
    app.include_router(manufacturing_reports_router)
    app.include_router(manufacturing_predictions_router)
    app.include_router(data_chat_router)
    app.mount("/static", StaticFiles(directory=settings.resolved_frontend_index_path.parent / "assets"), name="static")

    @app.get("/", include_in_schema=False)
    def frontend_entry() -> FileResponse:
        return FileResponse(settings.resolved_frontend_index_path)

    return app


app = create_app()
