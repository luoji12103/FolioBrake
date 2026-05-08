"""Configuration management with Redis-backed version control.

Stores each config snapshot in Redis with an incrementing version number.
Supports: get current, list history, rollback to a previous version.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any

from app.core.cache import get_redis

_CONFIG_PREFIX = "fb:config"
_VERSION_KEY = f"{_CONFIG_PREFIX}:version"
_SNAPSHOT_PREFIX = f"{_CONFIG_PREFIX}:snapshot"
_CURRENT_KEY = f"{_CONFIG_PREFIX}:current"


@dataclass
class ConfigSnapshot:
    version: int
    timestamp: float
    checksum: str
    data: dict[str, Any]


class ConfigCenter:
    """Redis-backed configuration store with full version history."""

    def __init__(self) -> None:
        self._local: dict[str, Any] = {}

    def _client(self):
        return get_redis()

    def _checksum(self, data: dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, key: str, default: Any = None) -> Any:
        return self._local.get(key, default)

    def set(self, key: str, value: Any) -> int:
        self._local[key] = value
        return self._persist()

    def update(self, values: dict[str, Any]) -> int:
        self._local.update(values)
        return self._persist()

    def load(self) -> dict[str, Any]:
        client = self._client()
        if client is None:
            return dict(self._local)
        raw: str | None = client.get(_CURRENT_KEY)  # type: ignore[assignment]
        if raw:
            snapshot = json.loads(raw)
            self._local = snapshot.get("data", {})
        return dict(self._local)

    def get_snapshot(self, version: int | None = None) -> ConfigSnapshot | None:
        client = self._client()
        if client is None:
            return None
        if version is None:
            raw: str | None = client.get(_CURRENT_KEY)  # type: ignore[assignment]
        else:
            raw = client.get(f"{_SNAPSHOT_PREFIX}:{version}")  # type: ignore[assignment]
        if not raw:
            return None
        d = json.loads(raw)
        return ConfigSnapshot(**d)

    def history(self, limit: int = 20) -> list[ConfigSnapshot]:
        client = self._client()
        if client is None:
            return []
        ver_raw: str | None = client.get(_VERSION_KEY)  # type: ignore[assignment]
        ver = int(ver_raw or 0)
        snapshots: list[ConfigSnapshot] = []
        for v in range(ver, max(ver - limit, 0), -1):
            raw: str | None = client.get(f"{_SNAPSHOT_PREFIX}:{v}")  # type: ignore[assignment]
            if raw:
                d = json.loads(raw)
                snapshots.append(ConfigSnapshot(**d))
        return snapshots

    def rollback(self, target_version: int) -> ConfigSnapshot | None:
        snapshot = self.get_snapshot(target_version)
        if snapshot is None:
            return None
        self._local = dict(snapshot.data)
        self._persist()
        return self.get_snapshot()

    def _persist(self) -> int:
        client = self._client()
        data = dict(self._local)
        checksum = self._checksum(data)

        if client is None:
            return 0

        ver: int = client.incr(_VERSION_KEY)  # type: ignore[assignment]
        snapshot = ConfigSnapshot(
            version=ver,
            timestamp=time.time(),
            checksum=checksum,
            data=data,
        )
        payload = json.dumps(asdict(snapshot), default=str)
        client.set(f"{_SNAPSHOT_PREFIX}:{ver}", payload)  # type: ignore[arg-type]
        client.set(_CURRENT_KEY, payload)  # type: ignore[arg-type]
        return ver


config_center = ConfigCenter()
