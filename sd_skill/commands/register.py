"""Registration flow (device-pair) + migration (paste existing Token)."""
from __future__ import annotations

import time

from sd_skill import client, config


def start() -> dict:
    """Create a new register session.

    Generates + persists a device_secret locally, posts to the backend, and
    returns {nonce, short_url, expires_at}. The agent should show short_url
    to the user and then repeatedly call `register-wait` until completed.
    """
    # Clear old pending state (in case a previous attempt was abandoned)
    config.clear_device_secret()
    secret = config.get_or_create_device_secret()

    r = client.post(
        "/api/v1/register/create-session",
        body={"device_secret": secret},
        with_auth=False,
    )
    if not r.ok:
        return {
            "status": "error",
            "code": r.error_code or "CREATE_SESSION_FAILED",
            "message": r.error_message or f"HTTP {r.status}",
        }
    return {
        "status": "pending",
        "nonce": r.data["nonce"],
        "short_url": r.data["short_url"],
        "expires_at": r.data["expires_at"],
        "hint": (
            "告诉用户打开 short_url 填表。填完后反复调用 `sd-skill register-wait` "
            "直到返回 status=completed 或 expired。"
        ),
    }


def wait(nonce: str, timeout_seconds: int = 30) -> dict:
    """Poll the register session until it completes, expires, or the timeout hits.

    Exponential backoff: 2s → 3s → 5s → 8s → 10s (cap). Max wait is
    ``timeout_seconds`` (per call; agent calls repeatedly).

    On completed: persist the token locally and return
    {status: 'completed', external_id, token_saved: true}.
    """
    if not nonce:
        return {"status": "error", "code": "BAD_ARGS", "message": "nonce required"}

    secret = config.get_device_secret()
    if not secret:
        return {
            "status": "error",
            "code": "NO_DEVICE_SECRET",
            "message": "call register-start first",
        }

    deadline = time.monotonic() + max(2, timeout_seconds)
    delay_schedule = [2, 3, 5, 8, 10]
    idx = 0

    while True:
        r = client.get(
            f"/api/v1/sessions/{nonce}/status",
            with_auth=False,
            headers={"X-Device-Secret": secret},
        )
        if r.status == 404:
            return {"status": "expired", "message": "session not found or expired"}
        if not r.ok:
            return {
                "status": "error",
                "code": r.error_code or "POLL_FAILED",
                "message": r.error_message or f"HTTP {r.status}",
            }
        body = r.data or {}
        s = body.get("status")
        if s == "completed":
            result = body.get("result") or {}
            token = result.get("token")
            external_id = result.get("external_id")
            if token:
                config.set_token(token)
            return {
                "status": "completed",
                "external_id": external_id,
                "token_saved": bool(token),
            }
        if s == "expired":
            return {"status": "expired"}

        # still pending — sleep and retry, unless timeout hit
        now = time.monotonic()
        if now >= deadline:
            return {"status": "pending", "message": "call me again"}
        delay = delay_schedule[min(idx, len(delay_schedule) - 1)]
        # don't sleep past the deadline
        delay = min(delay, max(1, int(deadline - now)))
        time.sleep(delay)
        idx += 1


def set_token_cmd(token: str) -> dict:
    """Migrate: save a Token that was obtained on another device."""
    t = (token or "").strip()
    if not t.startswith("sdt_"):
        return {
            "status": "error",
            "code": "BAD_TOKEN_FORMAT",
            "message": "token must start with 'sdt_'",
        }
    config.set_token(t)
    # Verify
    r = client.get("/api/v1/me")
    if not r.ok:
        config.clear_token()
        return {
            "status": "error",
            "code": r.error_code or "TOKEN_INVALID",
            "message": "token rejected by server; not saved",
        }
    me = r.data or {}
    return {
        "status": "ok",
        "external_id": me.get("external_id"),
        "message": "token saved locally and verified",
    }
