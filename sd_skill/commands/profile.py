"""User profile commands (whoami, reset-token, show-token, edit-profile-url)."""
from __future__ import annotations

import time

from sd_skill import client, config


def whoami() -> dict:
    """GET /me — return the caller's full profile."""
    r = client.get("/api/v1/me")
    if r.status == 401:
        return {"status": "unauthorized", "message": "no valid token; register first"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", "profile": r.data}


def reset_token() -> dict:
    """Invalidate old token, get a new one, save locally."""
    r = client.post("/api/v1/me/reset-token")
    if r.status == 401:
        return {"status": "unauthorized", "message": "no valid token"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    new_token = (r.data or {}).get("token")
    if new_token:
        config.set_token(new_token)
    return {
        "status": "ok",
        "token_saved": bool(new_token),
        "message": "new token saved; old one is now invalid",
    }


def show_token() -> dict:
    """Return the local Token plaintext (for backup)."""
    t = config.get_token()
    if not t:
        return {"status": "error", "code": "NO_TOKEN", "message": "no token saved locally"}
    return {"status": "ok", "token": t, "warning": "请妥善保存；泄露后其他人可冒充你"}


def edit_profile_url() -> dict:
    """Create an edit-profile session and return the form URL."""
    r = client.post("/api/v1/me/create-edit-profile-session")
    if r.status == 401:
        return {"status": "unauthorized", "message": "no valid token"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    d = r.data or {}
    return {
        "status": "ok",
        "nonce": d.get("nonce"),
        "short_url": d.get("short_url"),
        "expires_at": d.get("expires_at"),
        "hint": "告诉用户打开 short_url 填表，完成后可调用 `sd-skill profile-edit-poll <nonce>` 确认",
    }


def edit_profile_poll(nonce: str, timeout_seconds: int = 30) -> dict:
    """Poll an edit-profile session until completed or timeout."""
    if not nonce:
        return {"status": "error", "code": "BAD_ARGS", "message": "nonce required"}

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
                "updated_fields": (body.get("result") or {}).get("updated_fields", []),
            }
        now = time.monotonic()
        if now >= deadline:
            return {"status": "pending"}
        delay = delay_schedule[min(idx, len(delay_schedule) - 1)]
        delay = min(delay, max(1, int(deadline - now)))
        time.sleep(delay)
        idx += 1


def public_profile(external_id: str) -> dict:
    """Look up another user's public (redacted) profile by their 8-char ID."""
    ext = (external_id or "").strip().upper()
    if len(ext) != 8:
        return {"status": "error", "code": "BAD_ARGS", "message": "external_id must be 8 chars"}
    r = client.get(f"/api/v1/users/{ext}/public")
    if r.status == 404:
        return {"status": "not_found", "external_id": ext}
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", "profile": r.data}
