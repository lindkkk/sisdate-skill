"""CLI dispatcher — `python -m sd_skill <command> [args]` or `sd-skill <command>`.

Every command prints a JSON object to stdout. Exit code is 0 on any
'status' other than 'error' (agent-facing shell-friendly semantics).
"""
from __future__ import annotations

import argparse
import json
import sys

from sd_skill import config
from sd_skill.commands import browse, events, messages, profile, register


def _print(obj: dict) -> int:
    """Print JSON and return exit code based on status field."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()
    if obj.get("status") == "error":
        return 1
    return 0


def _require_token() -> dict | None:
    """Return an error dict if no token is set, else None."""
    if not config.get_token():
        return {
            "status": "needs_onboarding",
            "message": "本地没有 token。引导用户：A 注册（register-start）或 B 粘 token（set-token）",
        }
    return None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sd-skill",
        description="Sister-Date agent skill CLI. Every subcommand emits JSON to stdout.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # Config / status
    sub.add_parser("status", help="print local config state")
    spb = sub.add_parser("set-base-url", help="override API base URL")
    spb.add_argument("url")

    # Registration
    sub.add_parser("register-start", help="begin a new device-pair registration")
    spw = sub.add_parser("register-wait", help="poll the pending register session")
    spw.add_argument("nonce")
    spw.add_argument("--timeout", type=int, default=30)
    sst = sub.add_parser("set-token", help="migrate: save an existing Token locally")
    sst.add_argument("token")

    # Profile
    sub.add_parser("whoami", help="show current user's full profile")
    sub.add_parser("reset-token", help="invalidate old token + save new one")
    sub.add_parser("show-token", help="print local Token (for backup)")
    sub.add_parser("profile-edit-url", help="get a short URL to edit profile")
    spe = sub.add_parser("profile-edit-poll", help="poll an edit-profile session")
    spe.add_argument("nonce")
    spe.add_argument("--timeout", type=int, default=30)
    spp = sub.add_parser("user-public", help="look up another user by 8-char ID")
    spp.add_argument("external_id")

    # Events
    sub.add_parser("my-events", help="list my events (incl. expired/hidden)")
    smd = sub.add_parser("event-detail", help="get one event's full detail")
    smd.add_argument("event_id", type=int)
    sep = sub.add_parser("event-post-url", help="get a short URL to post a new event")
    see = sub.add_parser("event-edit-url", help="get a short URL to edit an event")
    see.add_argument("event_id", type=int)
    sed = sub.add_parser("event-delete", help="soft-delete one of my events")
    sed.add_argument("event_id", type=int)
    seo = sub.add_parser("event-poll", help="poll a post/edit event session")
    seo.add_argument("nonce")
    seo.add_argument("--timeout", type=int, default=30)

    # Browse
    sub.add_parser("browse", help="get the next matching event (consumes daily quota)")
    sub.add_parser("quota-left", help="show daily browse quota remaining")

    # Messages
    sms = sub.add_parser("send", help="send a station message to an 8-char ID")
    sms.add_argument("to_external_id")
    sms.add_argument("content", help="message content (wrap in quotes for spaces)")
    sub.add_parser("unread", help="unread message count")
    smi = sub.add_parser("inbox", help="list inbox messages")
    smi.add_argument("--limit", type=int, default=20)
    smi.add_argument("--offset", type=int, default=0)
    smo = sub.add_parser("outbox", help="list outbox messages")
    smo.add_argument("--limit", type=int, default=20)
    smo.add_argument("--offset", type=int, default=0)
    smr = sub.add_parser("msg", help="read one message (stamps read_at)")
    smr.add_argument("message_id", type=int)

    return p


# Commands that don't need a token (for pre-register / migration)
_UNAUTHED_COMMANDS = {
    "status",
    "set-base-url",
    "register-start",
    "register-wait",
    "set-token",
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.cmd

    # Most commands need a token
    if cmd not in _UNAUTHED_COMMANDS:
        err = _require_token()
        if err:
            return _print(err)

    if cmd == "status":
        return _print({"status": "ok", **config.status()})
    if cmd == "set-base-url":
        config.set_base_url(args.url)
        return _print({"status": "ok", "base_url": config.get_base_url()})

    if cmd == "register-start":
        return _print(register.start())
    if cmd == "register-wait":
        return _print(register.wait(args.nonce, args.timeout))
    if cmd == "set-token":
        return _print(register.set_token_cmd(args.token))

    if cmd == "whoami":
        return _print(profile.whoami())
    if cmd == "reset-token":
        return _print(profile.reset_token())
    if cmd == "show-token":
        return _print(profile.show_token())
    if cmd == "profile-edit-url":
        return _print(profile.edit_profile_url())
    if cmd == "profile-edit-poll":
        return _print(profile.edit_profile_poll(args.nonce, args.timeout))
    if cmd == "user-public":
        return _print(profile.public_profile(args.external_id))

    if cmd == "my-events":
        return _print(events.my_events())
    if cmd == "event-detail":
        return _print(events.detail(args.event_id))
    if cmd == "event-post-url":
        return _print(events.post_url())
    if cmd == "event-edit-url":
        return _print(events.edit_url(args.event_id))
    if cmd == "event-delete":
        return _print(events.delete_event(args.event_id))
    if cmd == "event-poll":
        return _print(events.poll_session(args.nonce, args.timeout))

    if cmd == "browse":
        return _print(browse.next_event())
    if cmd == "quota-left":
        return _print(browse.quota_left())

    if cmd == "send":
        return _print(messages.send(args.to_external_id, args.content))
    if cmd == "unread":
        return _print(messages.unread())
    if cmd == "inbox":
        return _print(messages.inbox(args.limit, args.offset))
    if cmd == "outbox":
        return _print(messages.outbox(args.limit, args.offset))
    if cmd == "msg":
        return _print(messages.read(args.message_id))

    return _print({"status": "error", "code": "UNKNOWN_CMD", "message": cmd})


if __name__ == "__main__":
    raise SystemExit(main())
