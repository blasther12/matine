from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import InMemoryRateLimiter
from app.core.security import RequestSecurityMiddleware
from app.modules.health.router import router as health_router
from app.modules.movies.router import router as movies_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = Database(resolved_settings.database_dsn)
        application.state.database = database
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(
        title="Matinê API",
        version="0.2.0",
        debug=resolved_settings.debug,
        docs_url=None,
        redoc_url=None,
        openapi_url=None if resolved_settings.is_production else "/openapi.json",
        lifespan=lifespan,
        redirect_slashes=False,
    )
    app.state.settings = resolved_settings
    app.state.catalog_rate_limiter = InMemoryRateLimiter(
        limit=resolved_settings.rate_limit_requests,
        window_seconds=resolved_settings.rate_limit_window_seconds,
    )

    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(movies_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    app.add_middleware(
        RequestSecurityMiddleware,
        environment=resolved_settings.app_env,
        trusted_hosts=resolved_settings.trusted_hosts,
    )

    return app


app = create_app()
