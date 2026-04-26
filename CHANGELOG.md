# CHANGELOG

## [0.2.0] — 2026-04-27 (thin-client refactor + chat command)

### Added
- `chat <message>` command — forwards user utterance to the new
  `/api/v1/chat` SSE endpoint and streams the LLM reply to stdout in
  real time. Tool invocations show as `[tool: name]` markers.
- `--history-json` flag on `chat` for multi-turn context (agent passes
  prior turns in Anthropic format).

### Changed
- **SKILL.md rewritten** for the v2 server-side LLM gateway. Old client-
  side intent routing is replaced by a 3-rule policy: (1) onboarding
  if no token, (2) local Token / config commands, (3) **everything
  else → `chat` transparent forward**. The Minimax model on the server
  now owns route classification, ref handling, application workflow,
  and fallback templates.
- Description in frontmatter updated to mention the application
  workflow (报名审批) and the薄客户端 architecture so OpenClaw / Claude
  Code agents pick the right behaviour.

### Preserved (backwards compatibility)
- All v0.1.x commands (`browse`, `send`, `inbox`, `event-post-url`,
  etc.) keep working as before. They serve as a fallback when the
  server LLM gateway is unreachable, and as a scripting interface for
  power users.

### Server compatibility
- Requires a sisdate-server running ≥ v0.2.0 (with the `/api/v1/chat`
  endpoint). The hosted instance at http://43.131.6.161 is on this
  version.

## [0.1.0] — 2026-04-19 (first public release)

### Added
- Full Python CLI (`sd_skill/`) wrapping the 17 sisdate backend API endpoints:
  - **Identity**: `register-start`, `register-wait`, `set-token`, `show-token`,
    `reset-token`
  - **Profile**: `whoami`, `profile-edit-url`, `profile-edit-poll`, `user-public`
  - **Events**: `my-events`, `event-detail`, `event-post-url`, `event-edit-url`,
    `event-delete`, `event-poll`
  - **Browse**: `browse`, `quota-left`
  - **Messages**: `send`, `unread`, `inbox`, `outbox`, `msg`
  - **Meta**: `status`, `set-base-url`
- `SKILL.md` aligned with [AgentSkills spec](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md):
  - Frontmatter: `name`, `description` (with rich "Use when..." triggers),
    `version: 0.1.0`, `metadata.openclaw` with `requires.bins`, `os`,
    `emoji`, `homepage`
  - Body: route A / route B / fallback intent classification,
    first-use branch (A register / B migrate), command-to-intent table,
    event card rendering template with enum-to-Chinese maps, few-shot
    examples for 姐姐端 + 弟弟端
- `README.md` with install instructions for OpenClaw (`~/.agents/skills/`),
  Claude Code (`~/.claude/skills/`), and generic agents (subprocess wrapper)
- `.clawhubignore` for publish hygiene
- ClawHub publish flow documented (login → diff → publish → version bump)

### Verified
- End-to-end tested against live http://43.131.6.161:
  - Register → form submit → poll → token saved
  - `whoami` returns full profile
  - `browse` returns events matching triple-constraint
  - `send` delivers station messages with constraint enforcement
  - `event-post-url` → form submit → poll → event_id

### Compatibility
- Python ≥ 3.10
- Single dependency: `httpx` ≥ 0.26
- OS: Linux / macOS / Windows
- Agents tested: Claude Code skill loader. OpenClaw compatibility expected
  per shared AgentSkills spec but awaiting field test.

## [0.0.1] — 2026-04-18 (scaffold)

- Placeholder README + LICENSE + .gitignore
