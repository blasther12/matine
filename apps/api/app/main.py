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
from app.modules.library.router import router as library_router
from app.modules.movies.router import router as movies_router
from app.modules.users.router import router as users_router


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
        version="0.3.0",
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
    route_prefix = "/api/backend" if resolved_settings.vercel_env is not None else ""
    app.include_router(health_router, prefix=route_prefix)
    app.include_router(movies_router, prefix=route_prefix)
    app.include_router(users_router, prefix=route_prefix)
    app.include_router(library_router, prefix=route_prefix)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Accept", "Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    app.add_middleware(
        RequestSecurityMiddleware,
        environment=resolved_settings.runtime_environment,
        trusted_hosts=resolved_settings.trusted_hosts,
    )

    return app


app = create_app()
