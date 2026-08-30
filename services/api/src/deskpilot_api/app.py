from fastapi import FastAPI

from . import __version__
from .middleware import request_context
from .errors import register_error_handlers
from .routes.health import router as health_router
from .routes.incidents import router as incident_router
from .routes.synthetic_control import router as synthetic_control_router
from .routes.guided_demo import router as guided_demo_router
from .openapi_contract import install_governed_openapi


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeskPilot API",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
    )
    app.middleware("http")(request_context)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(incident_router)
    app.include_router(synthetic_control_router)
    app.include_router(guided_demo_router)
    install_governed_openapi(app)
    return app


app = create_app()
