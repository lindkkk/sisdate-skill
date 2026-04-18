"""HTTP client wrapper for the sisdate API.

Thin layer over httpx with:
  * automatic base URL from config
  * automatic Bearer token injection when present
  * normalized result tuple: (status_code, json_body, text_body)
  * short retry on transient network errors
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from sd_skill.config import get_base_url, get_token


class Result:
    __slots__ = ("status", "data", "text", "headers")

    def __init__(self, status: int, data: Any, text: str, headers: dict):
        self.status = status
        self.data = data
        self.text = text
        self.headers = headers

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    @property
    def error_code(self) -> str | None:
        if isinstance(self.data, dict):
            err = self.data.get("error")
            if isinstance(err, dict):
                return err.get("code")
        return None

    @property
    def error_message(self) -> str:
        if isinstance(self.data, dict):
            err = self.data.get("error")
            if isinstance(err, dict):
                return err.get("message") or ""
        return self.text or ""


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=get_base_url(),
        timeout=20.0,
        trust_env=False,  # avoid broken SOCKS proxies from env
    )


def _do(
    method: str,
    path: str,
    *,
    json: Any = None,
    headers: dict | None = None,
    with_auth: bool = True,
    retries: int = 2,
) -> Result:
    hdrs = dict(headers or {})
    if with_auth:
        token = get_token()
        if token:
            hdrs.setdefault("Authorization", f"Bearer {token}")

    last_exc = None
    for attempt in range(retries + 1):
        try:
            with _client() as c:
                resp = c.request(method, path, json=json, headers=hdrs)
            try:
                body = resp.json() if resp.text else None
            except ValueError:
                body = None
            return Result(resp.status_code, body, resp.text, dict(resp.headers))
        except httpx.HTTPError as e:
            last_exc = e
            if attempt < retries:
                time.sleep(0.5 * (2**attempt))
                continue
    # All retries failed
    return Result(0, {"error": {"code": "NETWORK", "message": str(last_exc)}}, "", {})


# ---- Public helpers ----

def get(path: str, *, with_auth: bool = True, headers: dict | None = None) -> Result:
    return _do("GET", path, headers=headers, with_auth=with_auth)


def post(
    path: str, body: Any = None, *, with_auth: bool = True, headers: dict | None = None
) -> Result:
    return _do("POST", path, json=body, headers=headers, with_auth=with_auth)


def delete(path: str, *, with_auth: bool = True) -> Result:
    return _do("DELETE", path, with_auth=with_auth)
