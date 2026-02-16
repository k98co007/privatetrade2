from __future__ import annotations

import logging

from fastapi import FastAPI

from webapi.error_handler import register_exception_handlers
from webapi.middleware.cors import configure_cors
from webapi.middleware.request_context import configure_request_context
from webapi.routers.simulation_router import create_simulation_router
from webapi.routers.sse_router import create_sse_router
from webapi.services.report_facade import ReportFacade
from webapi.services.simulation_facade import SimulationFacade
from webapi.services.stream_session_manager import StreamSessionManager


LOGGER = logging.getLogger("webapi.bootstrap")


def _configure_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(title="PrivateTrade WEBAPI", version="1.0.0")
    LOGGER.info("app.create.start title=%s version=%s", app.title, app.version)
    configure_request_context(app)
    configure_cors(app)
    register_exception_handlers(app)

    stream_manager = StreamSessionManager()
    simulation_facade = SimulationFacade(stream_session_manager=stream_manager)
    report_facade = ReportFacade()

    app.include_router(create_simulation_router(simulation_facade=simulation_facade, report_facade=report_facade))
    app.include_router(create_sse_router(simulation_facade=simulation_facade, stream_session_manager=stream_manager))

    LOGGER.info("app.create.ready routers=%s", len(app.router.routes))

    return app


app = create_app()

__all__ = ["app", "create_app"]
