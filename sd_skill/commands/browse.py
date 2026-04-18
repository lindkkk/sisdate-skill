"""Browse: fetch the next matching activity (core UX)."""
from __future__ import annotations

from sd_skill import client


def next_event() -> dict:
    """GET /events/next. Returns one of:
      * {status: 'ok', event: {...}, quota_left: N}
      * {status: 'daily_limit_reached', quota_left: 0}
      * {status: 'empty_pool', quota_left: N}
      * {status: 'error', ...}
    """
    r = client.get("/api/v1/events/next")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return r.data or {"status": "error", "message": "empty response"}


def quota_left() -> dict:
    r = client.get("/api/v1/events/quota-left")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}
