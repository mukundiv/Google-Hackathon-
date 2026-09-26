"""SQLite persistence: learned weights, observed campaign results, API cache.

Kept deliberately small — the engine reads its world from the seed loader and
uses this only for state that accumulates while the console is running.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Column, Text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.config import get_settings

_settings = get_settings()
_engine = create_engine(_settings.database_url, echo=False, connect_args={"check_same_thread": False})


class WeightVersion(SQLModel, table=True):
    """A version of the Creator Opportunity Score weighting."""

    __tablename__ = "weight_version"

    id: int | None = Field(default=None, primary_key=True)
    version: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    weights_json: str = Field(sa_column=Column(Text))
    trained_on_campaigns: int = 0
    method: str = "baseline"
    note: str = ""

    @property
    def weights(self) -> dict[str, float]:
        return json.loads(self.weights_json)


class ObservedCampaign(SQLModel, table=True):
    """A campaign result fed back into the engine at runtime (the ACTIVATE ->
    OBSERVE half of the learning loop)."""

    __tablename__ = "observed_campaign"

    id: int | None = Field(default=None, primary_key=True)
    campaign_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_json: str = Field(sa_column=Column(Text))

    @property
    def payload(self) -> dict:
        return json.loads(self.payload_json)


class CacheEntry(SQLModel, table=True):
    """Live-provider response cache. Keeps the console working when a quota is
    exhausted or the network drops mid-demo."""

    __tablename__ = "cache_entry"

    key: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_json: str = Field(sa_column=Column(Text))


def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


def session() -> Session:
    return Session(_engine)


# --- cache helpers ------------------------------------------------------
def cache_get(key: str, ttl_seconds: int | None = None) -> Any | None:
    ttl = ttl_seconds if ttl_seconds is not None else _settings.cache_ttl_seconds
    with session() as s:
        entry = s.get(CacheEntry, key)
        if entry is None:
            return None
        created = entry.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created > timedelta(seconds=ttl):
            return None
        return json.loads(entry.payload_json)


def cache_get_stale(key: str) -> Any | None:
    """Ignore the TTL. Used as a last resort when a live call fails."""
    with session() as s:
        entry = s.get(CacheEntry, key)
        return json.loads(entry.payload_json) if entry else None


def cache_set(key: str, payload: Any) -> None:
    with session() as s:
        entry = s.get(CacheEntry, key)
        if entry:
            entry.payload_json = json.dumps(payload)
            entry.created_at = datetime.now(timezone.utc)
        else:
            entry = CacheEntry(key=key, payload_json=json.dumps(payload))
        s.add(entry)
        s.commit()


# --- weights ------------------------------------------------------------
def save_weights(version: str, weights: dict[str, float], trained_on: int, method: str, note: str) -> None:
    with session() as s:
        s.add(
            WeightVersion(
                version=version,
                weights_json=json.dumps(weights),
                trained_on_campaigns=trained_on,
                method=method,
                note=note,
            )
        )
        s.commit()


def list_weight_versions() -> list[WeightVersion]:
    with session() as s:
        return list(s.exec(select(WeightVersion).order_by(WeightVersion.id)))


def latest_weights() -> WeightVersion | None:
    versions = list_weight_versions()
    return versions[-1] if versions else None


# --- observed campaigns -------------------------------------------------
def add_observed_campaign(campaign_id: str, payload: dict) -> None:
    with session() as s:
        s.add(ObservedCampaign(campaign_id=campaign_id, payload_json=json.dumps(payload)))
        s.commit()


def list_observed_campaigns() -> list[dict]:
    with session() as s:
        rows = s.exec(select(ObservedCampaign).order_by(ObservedCampaign.id))
        return [r.payload for r in rows]


def reset_learning() -> None:
    """Return the engine to its baseline — used by the demo reset button."""
    with session() as s:
        for row in s.exec(select(ObservedCampaign)):
            s.delete(row)
        for row in s.exec(select(WeightVersion)):
            s.delete(row)
        s.commit()
