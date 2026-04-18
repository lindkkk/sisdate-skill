# CHANGELOG

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
