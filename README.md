# sisdate-skill

面向 Claude Code / Codex / Claude Desktop 等智能体代理的**姐弟恋约会活动匹配** Skill。

**核心规则**：同城 + 异性 + 女方至少比男方大 5 岁。每天最多推 2 条符合条件的活动给你。完全匿名，无用户名 / 密码 / 邮箱。

---

## 特性

- 🎯 **匿名**：Token 是唯一身份，无需用户名/密码/邮箱/实名
- 🪶 **零感知注册**：首次 30 秒填一张全下拉的网页表单即可
- 💬 **agent 对话驱动**：在 Claude Code 里说"有什么活动"就能刷，说"我想发"就能发
- 🔄 **跨设备迁移**：粘贴 Token 即可登录另一台设备
- 📬 **异步站内信**：用对方的 8 位 ID 发消息；服务端校验约束

## 依赖

- Python ≥ 3.10
- `httpx`（`pip install httpx` 或随本包自动安装）

## 安装

### Claude Code（主要目标）

```bash
# 把 skill 克隆到 Claude skills 目录
mkdir -p ~/.claude/skills
git clone https://github.com/lindkkk/sisdate-skill.git ~/.claude/skills/sisdate

# 安装 Python 依赖到你当前 Python 环境
cd ~/.claude/skills/sisdate && pip install -e .
```

重启 Claude Code。说一句"有什么约会活动"即可触发。

### 其他 agent（手动集成）

任何能执行 shell 命令的 agent 都能用。把本仓库 clone 到任意位置，安装依赖后：

```bash
python -m sd_skill <verb> [args]
```

相关 agent 配置提示：
- **Codex**（OpenAI）：把 `SKILL.md` 作为 system prompt 的一部分贴进去；命令清单见 `sd_skill/cli.py`。
- **Claude Desktop / Cursor**：把 SKILL.md 内容作为自定义 instruction 粘贴，或等本项目后续发布 MCP 版本。
- **自建 LangGraph / LlamaIndex**：用 `subprocess.run(["python", "-m", "sd_skill", ...])` 包装即可。

## 服务端

默认连接 `http://43.131.6.161`。可通过环境变量或配置覆盖：

```bash
# 环境变量（优先）
export SISDATE_API_BASE=https://your-deployment.example

# 或持久化
python -m sd_skill set-base-url https://your-deployment.example
```

## 命令清单（24 个，任何 agent 都能调）

### 身份与注册

| 命令 | 作用 |
|---|---|
| `status` | 显示本地配置（token 是否已存、base_url） |
| `register-start` | 发起一个新设备配对注册会话 |
| `register-wait <nonce> [--timeout N]` | 轮询注册会话是否完成（默认每次阻塞 30s） |
| `set-token <sdt_...>` | 粘贴已有 Token（跨设备迁移） |
| `reset-token` | 作废当前 Token 并发一个新的 |
| `show-token` | 打印本地 Token（供备份） |

### 资料

| 命令 | 作用 |
|---|---|
| `whoami` | 返回自己的完整资料 |
| `profile-edit-url` | 得到改资料的短链 |
| `profile-edit-poll <nonce>` | 轮询改资料完成 |
| `user-public <8-char-ID>` | 查别人的公开资料 |

### 活动

| 命令 | 作用 |
|---|---|
| `browse` | 按三重约束取下一条活动（消耗每日 2 次配额） |
| `quota-left` | 查今天还能看几条 |
| `my-events` | 列出我发过的活动（含过期 / 隐藏） |
| `event-detail <id>` | 看某个活动完整详情 |
| `event-post-url` | 得到"发新活动"的表单短链 |
| `event-edit-url <id>` | 得到"改活动"的表单短链 |
| `event-delete <id>` | 软删我的活动 |
| `event-poll <nonce>` | 轮询发/改活动会话完成 |

### 站内信

| 命令 | 作用 |
|---|---|
| `send <to_external_id> "<content>"` | 给 8 位 ID 发站内信 |
| `unread` | 未读计数 |
| `inbox [--limit N]` | 收件箱 |
| `outbox [--limit N]` | 发件箱 |
| `msg <message_id>` | 读一条消息（触发 read_at 标记） |

### 管理

| 命令 | 作用 |
|---|---|
| `set-base-url <url>` | 修改连的服务端 |

## 典型对话示例

```
用户: 最近有啥活动
Agent: 你是不是想找一个约会活动？是的话回复「是」或「看看」。
用户: 看看
Agent: [调 browse，渲染活动卡片]
       ┌─ #7 《周六外滩散步》
       │  姐姐 #R4DFRD77 · 38岁 · 上海
       │  想找个有趣的弟弟一起走走聊聊。
       │  时间：2026-05-04 15:00
       └─
       想参加？说「给 R4DFRD77 说 ...」。
       （你今天还能看 1 条）

用户: 给 R4DFRD77 说 周六我方便，可以加个微信吗
Agent: [调 send] ✅ 消息已送达 R4DFRD77。

用户: 我想发个自己的活动
Agent: [调 event-post-url] 打开下面的链接填表：
       http://43.131.6.161/e?c=GXW7S7
       填完我自动确认。
```

## 卸载

```bash
rm -rf ~/.claude/skills/sisdate
rm -rf ~/.config/sister-date   # 清本地 Token + device_secret
```

## 数据与隐私

- Token 存在 `~/.config/sister-date/token`（mode 600）
- device_secret 同目录，仅用于注册流程防抢占，之后可删除
- 所有业务数据在服务端。用户侧可见数据（活动、消息）100 天后不再展示；服务端为风险事件回溯保留。
- 不做实名 / 不采集设备信息 / 不追踪。完全匿名。

## License

MIT — see [LICENSE](./LICENSE).
