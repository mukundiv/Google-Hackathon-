"""Creator Opportunity Engine — API."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import services, store
from app.config import get_settings
from app.demo import default_brief
from app.providers.registry import get_providers
from app.routers import brand_routes, engine_routes, learning_routes
from app.schemas import HealthResponse, ProviderState


def _warm_cache() -> None:
    """Run the pipeline once so the first click is not a spinner.

    Scouting fits a momentum curve per trend, which costs a couple of seconds
    cold and nothing at all warm. Doing it at startup rather than on first
    request keeps a live demo responsive from the opening screen.
    """
    try:
        services.run_full(default_brief())
    except Exception:  # pragma: no cover - warming must never block startup
        logging.getLogger(__name__).warning("cache warm-up failed", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    threading.Thread(target=_warm_cache, daemon=True).start()
    yield


app = FastAPI(
    title="Creator Opportunity Engine",
    version="0.1.0",
    description=(
        "Turns Google and YouTube signals into creator investment decisions: "
        "Listen -> Predict -> Match -> Optimize -> Learn."
    ),
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(engine_routes.router)
app.include_router(brand_routes.router)
app.include_router(learning_routes.router)


@app.get("/api/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Which provider is actually serving each signal right now.

    The console renders this as a per-source badge, so nobody has to guess
    whether a number on screen came from a live API or the seeded world.
    """
    providers = get_providers()
    status = {k: ProviderState(**v) for k, v in providers.status_map().items()}
    return HealthResponse(
        status="ok",
        any_live=any(p.live for p in status.values()),
        providers=status,
        weights_version=services.weights_version(),
        activation_lead_days=services.activation_lead_days(),
        campaigns_in_ledger=len(services.all_campaigns()),
    )
