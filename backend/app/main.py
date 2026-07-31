from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.mount("/static", StaticFiles(directory=settings.resolved_frontend_index_path.parent / "assets"), name="static")

    @app.get("/", include_in_schema=False)
    def frontend_entry() -> FileResponse:
        return FileResponse(settings.resolved_frontend_index_path)

    return app


app = create_app()
