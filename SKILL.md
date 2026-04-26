---
name: sisdate
description: 姐弟恋 (sister-brother, age-gap ≥5 yr, female older) 约会活动匹配服务。用于当用户想找/浏览/发布约会活动、报名加入活动、或需要给已认识的 8 位 ID 发站内短信时。硬约束：同城 + 异性 + 女方至少比男方大 5 岁；每天最多浏览 2 条匹配活动。**v0.2.0 起这是一个薄客户端**：除了 token 本地操作和 session 轮询，所有用户对话都直接转发给服务端 LLM 网关（`chat` 命令），由服务端决定调哪个工具。Use when the user says things like "有什么活动 / 有啥 / 推荐 / 陪我 / 最近闷 / 想找点事做 / 约会" (找活动); "我想发活动 / 帮我约个周末 / 找人陪我吃饭" (发活动); "我想报名 #N / 加入活动 X" (报名审批); "有新消息吗 / 未读 / 收件" (查站内信); "给 XXXXXXXX 说 ..." 或 "给 #N 说 ..." (发站内信); "我的活动 / 我的报名 / 改活动 / 改资料 / 看 Token / 删活动" (账户/发帖管理). 对严格无关的闲聊一律由服务端 LLM 回固定拒识模板。
version: 0.2.0
metadata:
  openclaw:
    emoji: "💞"
    homepage: "https://github.com/lindkkk/sisdate-skill"
    requires:
      bins: ["python3"]
    os: ["linux", "macos", "windows"]
---

# sisdate — agent skill 说明（v0.2.0 薄客户端版）

## 核心理念变更

**v0.1.x（旧版）**：skill 内嵌完整意图路由 — agent 自己解析"用户说啥意思"再调具体命令（browse / send / event-post-url / ...）。

**v0.2.0（本版）**：skill 是**薄客户端**。把用户原话**原封不动**转发给服务端的 LLM 网关（住在 `http://43.131.6.161` 上的 Minimax 模型），由服务端 LLM 决定调哪个工具、怎么回应。skill 端只做不能在服务端做的事：本地 Token 保存 / session 配对码轮询。

## 路由规则（agent 行为简化为 3 条）

### 1. 本地无 token → 引导 onboarding
```
本地无 token 时（status 命令显示 token=null），询问用户：
  "欢迎！要新注册（A）还是粘贴已有 Token（B）？或直接粘 sdt_ 开头的 Token 自动识别 B。"
```
- 用户选 A 或表达"我新用户" → `python -m sd_skill register-start` → 把得到的 short_url 和 nonce 显示给用户 → `python -m sd_skill register-wait <nonce>` 阻塞轮询 → 拿到 token 后再继续
- 用户粘了 sdt_ 开头的字符串 → `python -m sd_skill set-token <token>` → 验证后继续
- 用户选 B 但没粘 token → 提示"请把 sdt_ 开头的 Token 粘过来"

### 2. 本地操作类 → 直接调对应命令
| 用户表达 | 命令 |
|---|---|
| "看我 Token / 备份码" | `show-token` |
| "重置 Token" | `reset-token` |
| "状态 / 配置" | `status` |
| "改服务端地址" | `set-base-url <url>` |

### 3. 其它一切 → 直接 chat 转发（**默认路径**）
对于**任何其它用户输入**（找活动、发活动、报名、发消息、闲聊、问天气、问"你是谁"……）：
```
python -m sd_skill chat "<原话原封不动>"
```
- chat 命令会流式打印服务端 LLM 的回答到 stdout（agent 应实时把这些字符传给用户）
- 如果服务端 LLM 调了工具（浏览、发消息、报名、审批等），stdout 会出现 `[tool: 工具名]` 标记
- chat 命令最后会输出 `---END---` + 一行 JSON 结果（含完整 reply 文本和 tool_calls 列表）
- agent 不需要解析这行 JSON，**只把 ---END--- 之前的所有字符**作为 LLM 回应展示给用户即可

## chat 调用示例

```bash
# 用户说"有什么活动"
python -m sd_skill chat "有什么活动"
# 输出（流式）：
你是不是想找一个约会活动？是的话回复「是」或「看看」；如果你想发起活动，请说「我想发活动」。
---END---
{"status":"ok","reply":"你是不是...","tool_calls":[],"stop_reason":"end_turn"}

# 用户回复"是"
python -m sd_skill chat "是"
# 输出：
[tool: browse_next_event]
┌─ 《周末外滩散步》
│  👩 #1 · 38岁 · 上海
│  ...
└─
---END---
{...}
```

## 会话历史（多轮对话）

服务端不持久化对话历史。agent 应在内存里保留最近的几轮 user/assistant 对话，每次 chat 调用时通过 `--history-json` 参数附上：

```bash
python -m sd_skill chat "再来一个" --history-json '[
  {"role":"user","content":"有什么活动"},
  {"role":"assistant","content":"你是不是想找..."},
  {"role":"user","content":"是"},
  {"role":"assistant","content":"┌─ 《周末外滩散步》..."}
]'
```

**最多保留 20 轮**（40 条消息）即可，超出由 agent 自己截断。

## 命令清单（兜底 / 高级用法）

老的 v0.1.x 命令全部保留，**用于 chat 端不可达时的兜底**或脚本化场景。日常对话不需要用：

### 身份 + 配置
- `status` / `set-base-url <url>` / `register-start` / `register-wait <nonce>` / `set-token <tok>` / `show-token` / `reset-token`

### 资料
- `whoami` / `profile-edit-url` / `profile-edit-poll <nonce>` / `user-public <8-char-id>`

### 活动（自己发的）
- `my-events` / `event-detail <id>` / `event-post-url` / `event-edit-url <id>` / `event-delete <id>` / `event-poll <nonce>`

### 浏览
- `browse` / `quota-left`

### 站内信
- `send <to_external_id> <content>` / `unread` / `inbox` / `outbox` / `msg <id>`

### v0.2.0 新增
- `chat <message> [--history-json '...']`

## 服务端

默认连 `http://43.131.6.161`。可用环境变量 `SISDATE_API_BASE` 或 `set-base-url` 覆盖。所有 token 存在 `~/.config/sister-date/token`。

## 兜底固定模板（仅当服务端 LLM 网关不可达时由 agent 直接回）

```
sisdate 服务暂时不可用。请稍后再试。
你可以先用本地命令查看：
- python -m sd_skill status   （本地配置）
- python -m sd_skill show-token  （备份 token）
```
