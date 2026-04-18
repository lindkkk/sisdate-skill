"""Local config for the skill.

State lives under ``~/.config/sister-date/`` (600 perms on sensitive files):
  * ``token``         — API token (plaintext sdt_...)
  * ``device_secret`` — random secret bound to a pending register session
  * ``base_url``      — optional override of API base URL

All files are small, plaintext, and only readable by the user.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from sd_skill import DEFAULT_API_BASE

CONFIG_DIR = Path.home() / ".config" / "sister-date"
TOKEN_FILE = CONFIG_DIR / "token"
DEVICE_SECRET_FILE = CONFIG_DIR / "device_secret"
BASE_URL_FILE = CONFIG_DIR / "base_url"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, 0o700)
    except OSError:
        pass


def _write(path: Path, value: str, mode: int = 0o600) -> None:
    _ensure_dir()
    path.write_text(value, encoding="utf-8")
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def _read(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


# ---- Token ----

def get_token() -> str | None:
    # Environment override takes precedence (useful for CI / scripted testing)
    env = os.environ.get("SISDATE_TOKEN")
    if env:
        return env.strip()
    return _read(TOKEN_FILE)


def set_token(token: str) -> None:
    _write(TOKEN_FILE, token)


def clear_token() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


# ---- Device secret (for registration flow) ----

def get_or_create_device_secret() -> str:
    existing = _read(DEVICE_SECRET_FILE)
    if existing:
        return existing
    new = secrets.token_urlsafe(32)
    _write(DEVICE_SECRET_FILE, new)
    return new


def get_device_secret() -> str | None:
    return _read(DEVICE_SECRET_FILE)


def clear_device_secret() -> None:
    if DEVICE_SECRET_FILE.exists():
        DEVICE_SECRET_FILE.unlink()


# ---- Base URL ----

def get_base_url() -> str:
    env = os.environ.get("SISDATE_API_BASE")
    if env:
        return env.rstrip("/")
    saved = _read(BASE_URL_FILE)
    if saved:
        return saved.rstrip("/")
    return DEFAULT_API_BASE


def set_base_url(url: str) -> None:
    _write(BASE_URL_FILE, url.rstrip("/"), mode=0o644)


# ---- Status snapshot ----

def status() -> dict:
    return {
        "base_url": get_base_url(),
        "token_set": get_token() is not None,
        "device_secret_set": get_device_secret() is not None,
        "config_dir": str(CONFIG_DIR),
    }
