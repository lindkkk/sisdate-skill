"""Station messaging: send, unread count, inbox/outbox, read."""
from __future__ import annotations

from sd_skill import client


def send(to_external_id: str, content: str) -> dict:
    ext = (to_external_id or "").strip().upper()
    if len(ext) != 8:
        return {"status": "error", "code": "BAD_ARGS", "message": "to_external_id must be 8 chars"}
    if not content or not content.strip():
        return {"status": "error", "code": "BAD_ARGS", "message": "content required"}
    r = client.post("/api/v1/messages", body={"to_external_id": ext, "content": content})
    if r.status == 401:
        return {"status": "unauthorized"}
    if r.status == 404 or r.error_code == "USER_NOT_FOUND":
        return {"status": "not_found", "message": f"user {ext} not found"}
    if r.status == 409 and r.error_code == "MESSAGE_CONSTRAINT_VIOLATION":
        return {
            "status": "constraint_violation",
            "message": "不符合匹配约束（同城 + 异性 + 年龄差≥5）",
        }
    if r.status == 409 and r.error_code == "MESSAGE_TARGET_BANNED":
        return {"status": "target_banned", "message": "对方账号已被封禁"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}


def unread() -> dict:
    r = client.get("/api/v1/messages/unread_count")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}


def inbox(limit: int = 20, offset: int = 0) -> dict:
    r = client.get(f"/api/v1/messages/inbox?limit={limit}&offset={offset}")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}


def outbox(limit: int = 20, offset: int = 0) -> dict:
    r = client.get(f"/api/v1/messages/outbox?limit={limit}&offset={offset}")
    if r.status == 401:
        return {"status": "unauthorized"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", **(r.data or {})}


def read(message_id: int) -> dict:
    r = client.get(f"/api/v1/messages/{message_id}")
    if r.status == 401:
        return {"status": "unauthorized"}
    if r.status == 404:
        return {"status": "not_found"}
    if not r.ok:
        return {"status": "error", "code": r.error_code, "message": r.error_message}
    return {"status": "ok", "message": r.data}
