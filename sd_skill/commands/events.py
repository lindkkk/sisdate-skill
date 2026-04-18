"""Event commands: my-events, detail, post/edit session URLs, delete, poll."""
from __future__ import annotations

import time

from sd_skill import client


def my_events(limit: int = 20, offset: int = 0) -> dict:
    """List the caller's own events (includes expired / hidden for history)."""
    r = client.get(f"/api/v1/events/mine?limit={limit}&offset={offset}")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}


def detail(event_id: int) -> dict:
    """Fetch one event's full detail."""
    r = client.get(f"/api/v1/events/{event_id}")
    if r.status == 404:
        return {"status": "not_found"}
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", "event": r.data}


def post_url() -> dict:
    """Create a post-event session; user fills form at short_url."""
    r = client.post("/api/v1/events/create-session")
    if r.status == 401:
        return {"status": "unauthorized"}
    if r.status == 409 or r.error_code == "EVENT_QUOTA_EXCEEDED":
        return {
            "status": "quota_exceeded",
            "message": "你已经有一个活跃的活动帖。先删除再发新的。",
        }
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    d = r.data or {}
    return {
        "status": "ok",
        "nonce": d.get("nonce"),
        "short_url": d.get("short_url"),
        "expires_at": d.get("expires_at"),
        "hint": "告诉用户打开 short_url 填表。完成后用 `sd-skill event-poll <nonce>` 等待确认。",
    }


def edit_url(event_id: int) -> dict:
    """Create an edit-event session for the given event_id."""
    r = client.post(f"/api/v1/events/{event_id}/edit-session")
    if r.status == 401:
        return {"status": "unauthorized"}
    if r.status == 403:
        return {"status": "forbidden", "message": "not the event owner"}
    if r.status == 404:
        return {"status": "not_found"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    d = r.data or {}
    return {
        "status": "ok",
        "nonce": d.get("nonce"),
        "short_url": d.get("short_url"),
        "expires_at": d.get("expires_at"),
    }


def delete_event(event_id: int) -> dict:
    """Soft-delete (hide) one of the caller's events. Backend keeps the row."""
    r = client.delete(f"/api/v1/events/{event_id}")
    if r.status == 401:
        return {"status": "unauthorized"}
    if r.status == 403:
        return {"status": "forbidden"}
    if r.status == 404:
        return {"status": "not_found"}
    if r.status == 204:
        return {"status": "ok", "message": "event hidden"}
    return {"status": "error", "code": r.error_code, "message": r.error_message}


def poll_session(nonce: str, timeout_seconds: int = 30) -> dict:
    """Poll an event post/edit session until it completes or times out."""
    if not nonce:
        return {"status": "error", "code": "BAD_ARGS"}

    deadline = time.monotonic() + max(2, timeout_seconds)
    delay_schedule = [2, 3, 5, 8, 10]
    idx = 0
    while True:
        r = client.get(f"/api/v1/sessions/{nonce}/status")
        if r.status == 404:
            return {"status": "expired"}
        if not r.ok:
            return {"status": "error", "code": r.error_code, "message": r.error_message}
        body = r.data or {}
        s = body.get("status")
        if s == "completed":
            return {
                "status": "completed",
                "event_id": (body.get("result") or {}).get("event_id"),
            }
        now = time.monotonic()
        if now >= deadline:
            return {"status": "pending"}
        delay = min(delay_schedule[min(idx, len(delay_schedule) - 1)],
                    max(1, int(deadline - now)))
        time.sleep(delay)
        idx += 1
