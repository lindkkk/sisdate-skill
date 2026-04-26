"""Chat command (skill v0.2.0): forward user utterance to /api/v1/chat
and print the streamed assistant reply to stdout in real time.

Designed for agent runtimes that capture stdout — each token chunk is
written immediately so the agent can show streaming output to its
caller. Tool-use events are written as ``[tool: name]`` markers.

History is **not** persisted client-side; the agent passes whatever
prior turns it wants the server LLM to consider. For long sessions an
agent may track the last N turns itself and supply them via a separate
mechanism (future v0.3.0: --history-file flag).
"""
from __future__ import annotations

import json
import sys
from typing import Iterator

import httpx

from sd_skill.config import get_base_url, get_token


def _sse_events(resp: httpx.Response) -> Iterator[tuple[str, dict]]:
    """Yield (event_type, parsed_data) tuples from an SSE response stream."""
    buf = ""
    for chunk in resp.iter_text():
        if not chunk:
            continue
        buf += chunk
        while "\n\n" in buf:
            raw, buf = buf.split("\n\n", 1)
            ev_type = "message"
            data_lines: list[str] = []
            for line in raw.splitlines():
                if line.startswith("event: "):
                    ev_type = line[7:].strip()
                elif line.startswith("data: "):
                    data_lines.append(line[6:])
            if not data_lines:
                continue
            try:
                payload = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                continue
            yield ev_type, payload


def chat(message: str, history: list[dict] | None = None) -> dict:
    """Send one message to the chat endpoint and stream the reply.

    Returns a final summary dict for JSON-mode callers that don't capture
    stdout streaming. The visible streaming output goes to stdout as it
    arrives; the dict result also contains the full assembled assistant
    text under ``reply``.
    """
    token = get_token()
    if not token:
        return {
            "status": "error",
            "code": "NEEDS_AUTH",
            "message": "本地无 token，先 register-start 或 set-token",
        }

    body: dict = {"message": message}
    if history:
        body["history"] = history

    reply_parts: list[str] = []
    tool_calls: list[dict] = []
    error_msg: str | None = None
    stop_reason: str | None = None

    try:
        with httpx.Client(
            base_url=get_base_url(),
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            trust_env=False,
        ) as client:
            with client.stream(
                "POST",
                "/api/v1/chat",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            ) as resp:
                if resp.status_code != 200:
                    text = resp.read().decode("utf-8", errors="replace")
                    return {
                        "status": "error",
                        "code": f"HTTP_{resp.status_code}",
                        "message": text[:500],
                    }
                for ev_type, payload in _sse_events(resp):
                    if ev_type == "text":
                        chunk = payload.get("data", "")
                        if chunk:
                            reply_parts.append(chunk)
                            sys.stdout.write(chunk)
                            sys.stdout.flush()
                    elif ev_type == "tool":
                        tool_calls.append(payload)
                        sys.stdout.write(f"\n[tool: {payload.get('name', '?')}]\n")
                        sys.stdout.flush()
                    elif ev_type == "error":
                        error_msg = payload.get("message", "unknown error")
                        sys.stdout.write(f"\n[error: {error_msg}]\n")
                        sys.stdout.flush()
                    elif ev_type == "done":
                        stop_reason = payload.get("stop_reason")
    except httpx.HTTPError as e:
        return {"status": "error", "code": "NETWORK", "message": str(e)}

    sys.stdout.write("\n")
    sys.stdout.flush()

    result = {
        "status": "ok" if error_msg is None else "error",
        "reply": "".join(reply_parts),
        "tool_calls": tool_calls,
        "stop_reason": stop_reason,
    }
    if error_msg:
        result["message"] = error_msg
    return result
