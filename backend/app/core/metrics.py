"""Prometheus metrics for monitoring and observability.

Exposes:
  - /metrics endpoint returning Prometheus text format
  - Pre-defined counters, histograms, and gauges for HTTP, DB, and business logic
"""

from __future__ import annotations

import time
from typing import Callable

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    multiprocess,
    CONTENT_TYPE_LATEST,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ── Application info ────────────────────────────────────────────────────────
APP_INFO = Info("folio_brake", "Retail ETF Guardian application info")
APP_INFO.info({"version": "0.1.0", "environment": "dev"})

# ── HTTP metrics ────────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# ── Database metrics ────────────────────────────────────────────────────────
DB_CONNECTIONS = Gauge(
    "db_active_connections",
    "Active database connections",
)

DB_QUERY_LATENCY = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# ── Business metrics ────────────────────────────────────────────────────────
DATA_SYNC_COUNT = Counter(
    "data_sync_total",
    "Total data sync operations",
    ["symbol", "status"],
)

RISK_STATE_CHANGES = Counter(
    "risk_state_changes_total",
    "Total risk state transitions",
    ["from_state", "to_state"],
)

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Total rate limit rejections",
)


# ── Metrics middleware ──────────────────────────────────────────────────────


def _normalise_path(path: str) -> str:
    """Collapse path parameters into placeholders for cardinality control."""
    parts = path.strip("/").split("/")
    normalised: list[str] = []
    for part in parts:
        # Collapse numeric / UUID segments
        if part.isdigit() or (len(part) == 36 and part.count("-") == 4):
            normalised.append("{id}")
        else:
            normalised.append(part)
    return "/" + "/".join(normalised) if normalised else "/"


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records request count, latency, and in-flight gauge for every HTTP call."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        endpoint = _normalise_path(request.url.path)

        # Skip the metrics endpoint itself to avoid noise
        if endpoint == "/metrics":
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status_code=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
            return response
        except Exception:
            elapsed = time.perf_counter() - start
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=500).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
            raise
        finally:
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


# ── /metrics endpoint helper ───────────────────────────────────────────────


def get_metrics_response() -> Response:
    """Return a Starlette ``Response`` with the latest Prometheus scrape data."""
    registry = REGISTRY
    # Support prometheus multiprocess mode when env var is set
    if "PROMETHEUS_MULTIPROC_DIR" in __import__("os").environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    body = generate_latest(registry)
    return Response(content=body, media_type=CONTENT_TYPE_LATEST)
