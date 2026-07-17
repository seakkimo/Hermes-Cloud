# Project Hermes-CLOUD — 建構 SOP

> 個人 AI 作業系統，從 Telegram Bot 出發，逐步擴展至多模型、記憶體、排程、新聞、論文、瀏覽器、MCP、機器人控制。

---

## 目錄

- [環境前置準備](#0-環境前置準備)
- [V0.1 — Telegram + OpenRouter](#v01--telegram--openrouter)
- [V0.2 — 多模型切換](#v02--多模型切換)
- [V0.3 — Supabase 記憶體](#v03--supabase-記憶體)
- [V0.4 — GitHub Actions 排程器](#v04--github-actions-排程器)
- [V0.5 — News Agent](#v05--news-agent)
- [V0.6 — Paper Agent](#v06--paper-agent)
- [V0.7 — Browser Agent](#v07--browser-agent)
- [V0.8 — MCP Server](#v08--mcp-server)
- [V0.9 — Robot Tool (Bridge Agent)](#v09--robot-tool-bridge-agent)

---

## 0. 環境前置準備

### 需要的帳號與 API Key

| 服務 | 用途 | 取得方式 |
|------|------|----------|
| Telegram BotFather | Bot Token | `@BotFather` → `/newbot` |
| OpenRouter | LLM API | https://openrouter.ai |
| Supabase | 對話記憶體 | https://supabase.com |
| Render | 雲端部署 | https://render.com |
| GitHub | 原始碼 + Actions | https://github.com |
| Tavily | 網路搜尋 | https://tavily.com |

### 本地開發環境

```bash
# Python 3.11+
python --version

# 建立虛擬環境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 專案結構

```
Hermes_Cloud/
├── main.py                  # FastAPI 入口
├── config/settings.py       # 所有環境變數
├── src/
│   ├── telegram/bot.py      # Telegram 指令處理
│   ├── llm/openrouter.py    # LLM 呼叫層
│   ├── agent/runtime.py     # Agent 主邏輯
│   ├── agent/session.py     # 使用者 Session
│   ├── memory/supabase.py   # 對話記憶體
│   ├── tools/browser.py     # 搜尋 + 網頁擷取
│   ├── tools/news.py        # 新聞 Agent
│   ├── tools/paper.py       # 論文 Agent
│   └── mcp/                 # MCP Server
│       ├── registry.py
│       └── tools.py
├── bridge/bridge_agent.py   # ROS2 Bridge Agent (本地 WSL2)
├── docker/Dockerfile
├── .github/workflows/       # GitHub Actions
└── requirements.txt
```

### `.env` 設定

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_token

# OpenRouter
OPENROUTER_API_KEY=your_key
OPENROUTER_DEFAULT_MODEL=google/gemma-4-31b-it:free

# App
APP_ENV=development          # production = webhook mode
LOG_LEVEL=INFO

# Supabase (V0.3+)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
MEMORY_MAX_MESSAGES=20

# Search (V0.7+)
TAVILY_API_KEY=your_key
DEFAULT_SEARCH_ENGINE=tavily

# Scheduler (V0.4+)
SCHEDULER_SECRET=your_secret
TELEGRAM_OWNER_CHAT_ID=your_chat_id

# Render (V0.4+)
RENDER_EXTERNAL_URL=https://your-app.onrender.com
PORT=8000
```

---

## V0.1 — Telegram + OpenRouter

### 架構

```
User → Telegram → Bot (polling) → OpenRouter → LLM → Reply
```

### 核心檔案

**`config/settings.py`** — 讀取環境變數，定義 fallback 模型鏈（21 個免費模型 + deepseek-r1 付費備援）

**`src/llm/openrouter.py`** — 使用 `AsyncOpenAI` 呼叫 OpenRouter，`fallback=True` 時自動嘗試整條鏈

```python
async def chat(messages, model=DEFAULT_MODEL, fallback=True) -> str:
    candidates = [model] + [m for m in FALLBACK_MODELS if m != model] if fallback else [model]
    for candidate in candidates:
        try:
            response = await _client.chat.completions.create(model=candidate, messages=messages)
            return response.choices[0].message.content
        except (RateLimitError, NotFoundError):
            if not fallback: raise
            # try next model
    raise RuntimeError("All models unavailable.")
```

**`src/agent/runtime.py`** — 組裝 system prompt + 歷史訊息，呼叫 LLM

**`src/telegram/bot.py`** — 處理 `/start` 與一般訊息

**`main.py`** — `APP_ENV=development` 時用 polling，`production` 時用 webhook (FastAPI)

### 安裝

```bash
pip install python-telegram-bot openai python-dotenv fastapi uvicorn
```

### 驗證

```bash
python main.py
# 預期輸出：Starting in polling mode (local)
```

Telegram 傳送任意訊息 → Bot 回覆 ✅

---

## V0.2 — 多模型切換

### 新增功能

- `/model list` — 列出所有可用模型別名
- `/model <alias>` — 切換指定模型（失敗不 fallback）
- `/model auto` — 回到自動 fallback 模式

### 架構

新增 `src/agent/session.py`，以 `user_id` 為 key 的 in-memory dict 儲存每位使用者的模型選擇。

```python
AUTO_MODEL = "__auto__"
_sessions: dict[int, dict] = {}
```

`runtime.py` 根據 `is_auto(user_id)` 決定是否啟用 fallback：

```python
if is_auto(user_id):
    reply = await chat(messages)               # fallback=True
else:
    reply = await chat(messages, model=model, fallback=False)  # 失敗直接報錯
```

### 模型別名表（共 21 個）

| 別名 | 模型 ID |
|------|---------|
| `gemma` | `google/gemma-4-31b-it:free` |
| `llama` | `meta-llama/llama-4-scout:free` |
| `deepseek` | `deepseek/deepseek-r1` (付費) |
| `qwen` | `qwen/qwen3-coder:free` |
| `mistral` | `mistralai/mistral-7b-instruct:free` |
| ... | （完整列表見 `config/settings.py`） |

### 驗證

```
/model list        → 顯示所有別名與當前模型
/model gemma       → ✅ Switched to google/gemma-4-31b-it:free
/model auto        → ✅ Switched to auto mode
```

---

## V0.3 — Supabase 記憶體

### 架構

```
每次對話 → load_history(user_id) → 加入 messages → LLM → save_message()
```

### Supabase 設定

1. 建立 Supabase 專案
2. SQL Editor 執行：

```sql
CREATE TABLE conversations (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL,
  role        TEXT NOT NULL,       -- 'user' | 'assistant'
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 啟用 RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Service role 可完整存取（後端使用 service_role key）
CREATE POLICY "service_role_all" ON conversations
  USING (true) WITH CHECK (true);
```

3. 取得 `SUPABASE_URL` 與 `SUPABASE_SERVICE_KEY`（Settings → API → service_role）

### 核心程式碼 `src/memory/supabase.py`

```python
async def load_history(user_id: int) -> list[dict]:
    result = client.table("conversations")
        .select("role, content")
        .eq("user_id", user_id)
        .order("created_at")
        .limit(MEMORY_MAX_MESSAGES)
        .execute()
    return [{"role": r["role"], "content": r["content"]} for r in result.data]
```

### 新增指令

- `/clear` — 清除該使用者的對話歷史

### 安裝

```bash
pip install supabase==2.10.0
```

### 驗證

1. 傳送幾則訊息
2. 重啟 Bot，再問「我剛才說了什麼？」→ Bot 能記得 ✅
3. `/clear` → 再問 → Bot 不記得 ✅

---

## V0.4 — GitHub Actions 排程器

### 架構

```
GitHub Actions (cron) → POST /task → Render → 執行任務
```

### Render 部署設定

1. GitHub repo 連接 Render
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python main.py`
4. 環境變數：填入所有 `.env` 內容，`APP_ENV=production`

### Webhook 模式 (`main.py`)

```python
if APP_ENV == "production":
    run_webhook()   # FastAPI + uvicorn
else:
    run_polling()   # python-telegram-bot polling
```

Webhook 啟動時自動呼叫：
```python
await tg_app.bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
```

### GitHub Actions Secrets 設定

| Secret | 值 |
|--------|----|
| `RENDER_URL` | `https://your-app.onrender.com` |
| `SCHEDULER_SECRET` | 自訂密鑰 |
| `SUPABASE_URL` | Supabase 專案 URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |

### Keep-Alive (`.github/workflows/keep_alive.yml`)

每 14 分鐘 ping 一次，防止 Render Free tier 休眠：

```yaml
on:
  schedule:
    - cron: "*/14 * * * *"
```

### 驗證

```bash
# 手動觸發 workflow
# GitHub → Actions → Keep Alive → Run workflow
# 預期：curl 回傳 {"status":"alive"}
```

`/ping` endpoint 回傳 `{"status": "alive"}` ✅

---

## V0.5 — News Agent

### 架構

```
GitHub Actions (08:00 UTC+8) → POST /task {"task":"news"}
→ news.run() → Google News RSS → LLM 中文摘要 → Telegram
```

### 核心程式碼 `src/tools/news.py`

- 來源：Google News RSS（AI + Robotics 兩個 feed）
- 每個 feed 取前 5 則標題
- 用 LLM 整理成繁體中文摘要

```python
FEEDS = {
    "AI": "https://news.google.com/rss/search?q=artificial+intelligence&hl=zh-TW...",
    "Robotics": "https://news.google.com/rss/search?q=robotics&hl=zh-TW...",
}
```

### 安裝

```bash
pip install feedparser==6.0.11
```

### GitHub Actions (`.github/workflows/scheduler.yml`)

```yaml
on:
  schedule:
    - cron: "0 0 * * *"   # 00:00 UTC = 08:00 UTC+8
```

### 驗證

```bash
# 手動觸發或直接 curl
curl -X POST https://your-app.onrender.com/task \
  -H "Content-Type: application/json" \
  -H "x-scheduler-secret: YOUR_SECRET" \
  -d '{"task": "news"}'
```

Telegram 收到 `📰 今日科技新聞摘要` ✅

---

## V0.6 — Paper Agent

### 架構

```
GitHub Actions (08:30 UTC+8) → POST /task {"task":"paper"}
→ paper.run() → arXiv API → LLM 中文摘要 → Telegram
```

### 核心程式碼 `src/tools/paper.py`

- 來源：arXiv（AI / Robotics / UAV 三個主題）
- 每個主題取最新 3 篇
- LLM 每篇一句話摘要 + 保留連結

```python
TOPICS = {
    "AI": "artificial intelligence machine learning",
    "Robotics": "robotics",
    "無人機": "UAV drone autonomous aerial vehicle",
}
```

### 安裝

```bash
pip install arxiv==2.1.3
```

### GitHub Actions (`.github/workflows/paper_agent.yml`)

```yaml
on:
  schedule:
    - cron: "30 0 * * *"   # 00:30 UTC = 08:30 UTC+8
```

### 驗證

```bash
curl -X POST https://your-app.onrender.com/task \
  -H "Content-Type: application/json" \
  -H "x-scheduler-secret: YOUR_SECRET" \
  -d '{"task": "paper"}'
```

Telegram 收到 `📄 今日論文摘要` ✅

---

## V0.7 — Browser Agent

### 架構

```
User → /browse <url>      → Jina Reader → LLM 摘要
User → /browse <keywords> → Search Engine → LLM 回答
User → 含關鍵字的訊息     → 自動觸發搜尋
```

### 搜尋引擎

| 引擎 | 說明 | 限制 |
|------|------|------|
| `tavily` | Tavily API，通用搜尋 | 1000 req/月（免費） |
| `news` | Google News RSS | 無限制，僅新聞 |

### 核心程式碼 `src/tools/browser.py`

```python
# 網頁擷取：Jina Reader
async def fetch_page(url: str) -> str:
    response = await client.get(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
    return response.text[:3000]

# 統一搜尋介面
async def search(query: str, engine: str = "tavily") -> list[dict]:
    if engine == "news":
        return await search_news(query)
    return await search_tavily(query)
```

### 自動搜尋關鍵字觸發 (`src/agent/runtime.py`)

```python
SEARCH_KEYWORDS = ["今天", "今日", "最新", "最近", "新聞", "搜尋", "查一下",
                   "latest", "recent", "today", "news", "search", ...]
```

### 新增指令

- `/browse <url>` — 擷取並摘要網頁
- `/browse <keywords>` — 強制搜尋
- `/search list` — 列出搜尋引擎
- `/search <engine>` — 切換搜尋引擎

### 安裝

```bash
pip install httpx tavily-python beautifulsoup4
```

### 驗證

```
/browse https://openai.com   → 回傳網頁摘要 ✅
/browse latest AI news       → 回傳搜尋結果摘要 ✅
/search news                 → ✅ Search engine switched to news
今天有什麼 AI 新聞？          → 自動觸發搜尋 ✅
```

---

## V0.8 — MCP Server

### 架構

```
Cline (IDE) → streamable-http → POST /mcp → Tool Registry → 執行工具
```

### MCP 工具列表

| 工具名稱 | 功能 |
|----------|------|
| `search` | Tavily / Google News 搜尋 |
| `browse` | Jina Reader 擷取網頁 |
| `get_memory` | 讀取 Supabase 對話歷史 |
| `news_summary` | 取得今日新聞摘要 |
| `robot_command` | 傳送指令給 Bridge Agent |

### 核心程式碼

**`src/mcp/registry.py`** — Tool dataclass + register/call 機制

```python
@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: dict

async def call_tool(name: str, arguments: dict) -> Any:
    tool = get_tool(name)
    return await tool.func(**arguments)
```

**`main.py` MCP endpoint** — 完整 JSON-RPC 2.0 格式

```python
@web.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.json()
    method = body.get("method")
    # 處理 initialize / tools/list / tools/call
```

**SSE GET endpoint** — Cline streamable-http 需要：

```python
@web.get("/mcp")
async def mcp_sse(request: Request):
    async def event_stream():
        yield "event: endpoint\ndata: /mcp\n\n"
        while True:
            yield ": keep-alive\n\n"
            await asyncio.sleep(15)
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### Cline 設定

`~/.cline/mcp_settings.json`（或 Cline UI → MCP Servers → Add）：

```json
{
  "mcpServers": {
    "hermes": {
      "type": "streamable-http",
      "url": "https://your-app.onrender.com/mcp"
    }
  }
}
```

### 驗證

1. Cline → MCP Servers → hermes → 狀態顯示 connected ✅
2. 在 Cline 對話中呼叫 `search` 工具 → 回傳搜尋結果 ✅
3. 呼叫 `news_summary` → 回傳新聞摘要 ✅

---

## V0.9 — Robot Tool (Bridge Agent)

### 架構

```
Telegram / Cline
      ↓
Hermes Cloud (Render) — /ws/robot WebSocket
      ↓  (wss://)
Bridge Agent (WSL2 本地)
      ↓  (ROS2 Topic)
/cmd_vel → Gazebo / 實體機器人
```

### WSL2 環境安裝

#### 1. 安裝 WSL2 + Ubuntu 24.04

```powershell
# Windows PowerShell (管理員)
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

#### 2. 安裝 ROS2 Jazzy

```bash
# 設定 locale
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# 加入 ROS2 apt repo
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list

# 安裝 ROS2 Jazzy
sudo apt update
sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions

# 加入 bashrc
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### 驗證 ROS2

```bash
ros2 topic list
# 預期輸出：
# /parameter_events
# /rosout
```

#### 3. 安裝 Gazebo Harmonic

```bash
sudo apt install -y ros-jazzy-ros-gz
gz sim --version
# 預期：Gazebo Harmonic v8.11.0
```

#### 4. 建立 Bridge Agent 虛擬環境

> ⚠️ 必須在 WSL2 home 目錄建立，不能在 `/mnt/d`（Windows 掛載路徑有權限問題）
> ⚠️ WSL2 重開機後 venv 可能消失，若出現 `No such file or directory` 請重新執行以下步驟

```bash
cd ~
python3 -m venv hermes-bridge --system-site-packages
# --system-site-packages 讓 venv 可存取系統的 rclpy / numpy
source ~/hermes-bridge/bin/activate

pip install websockets==13.1
```

### Bridge Agent 程式碼 `bridge/bridge_agent.py`

```python
class RobotController(Node):
    def __init__(self):
        super().__init__("hermes_bridge")
        self.cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)

    def move(self, linear_x=0.0, angular_z=0.0):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel.publish(msg)
```

支援的動作：

| action | linear_x | angular_z |
|--------|----------|-----------|
| `move_forward` | +speed | 0 |
| `move_backward` | -speed | 0 |
| `turn_left` | 0 | +speed |
| `turn_right` | 0 | -speed |
| `stop` | 0 | 0 |

### Render 端 WebSocket endpoint (`main.py`)

```python
@web.websocket("/ws/robot")
async def robot_ws(websocket: WebSocket):
    await websocket.accept()
    _robot_ws = websocket
    # 持續接收 Bridge Agent 回傳的狀態
    async for data in websocket.iter_text():
        logger.info(f"Robot status: {data}")
```

### 啟動 Bridge Agent

> 每次重新啟動 WSL2 都需要執行以下完整步驟

```bash
# WSL2 terminal — 每次啟動順序不能錯
source /opt/ros/jazzy/setup.bash
source ~/hermes-bridge/bin/activate
cd /mnt/d/Hermes_Cloud/bridge

python3 bridge_agent.py
```

預期輸出：
```
2026-07-12 12:42:22 | INFO | ROS2 node initialized
2026-07-12 12:42:22 | INFO | Connecting to wss://hermes-cloud-y1i2.onrender.com/ws/robot
2026-07-12 12:42:23 | INFO | Connected to Hermes Cloud
```

確認 Render 端連線狀態：
```bash
curl https://hermes-cloud-y1i2.onrender.com/ws/robot/status
# 預期：{"connected": true}
```

### 驗證 Bridge Agent ✅

> ⚠️ Render Free tier 每次重新部署後 WebSocket 連線會斷開，需重新啟動 Bridge Agent

#### 步驟 1：確認 WebSocket 連線狀態

```bash
curl https://hermes-cloud-y1i2.onrender.com/ws/robot/status
# 預期：{"connected": true}
```

#### 步驟 2：WSL2 開新 terminal 監聽 /cmd_vel

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /cmd_vel
```

#### 步驟 3：傳送機器人指令

```bash
# move_forward
curl -X POST https://hermes-cloud-y1i2.onrender.com/task \
  -H "Content-Type: application/json" \
  -H "x-scheduler-secret: YOUR_SCHEDULER_SECRET" \
  -d '{"task": "robot_command", "params": {"command": {"action": "move_forward", "speed": 0.3}}}'
# 預期：{"status": "ok", "task": "robot_command", "result": "Command sent: {'action': 'move_forward', 'speed': 0.3}"}

# turn_left
curl -X POST https://hermes-cloud-y1i2.onrender.com/task \
  -H "Content-Type: application/json" \
  -H "x-scheduler-secret: YOUR_SCHEDULER_SECRET" \
  -d '{"task": "robot_command", "params": {"command": {"action": "turn_left", "speed": 0.5}}}'

# stop
curl -X POST https://hermes-cloud-y1i2.onrender.com/task \
  -H "Content-Type: application/json" \
  -H "x-scheduler-secret: YOUR_SCHEDULER_SECRET" \
  -d '{"task": "robot_command", "params": {"command": {"action": "stop"}}}'
```

#### 步驟 4：確認 /cmd_vel 輸出（實測結果）

```
linear:
  x: 0.3   ← move_forward
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0
---
linear:
  x: 0.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5   ← turn_left
---
linear:
  x: 0.0   ← stop
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0
---
```

#### 步驟 5：Gazebo 視覺化測試（選用）

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

---

## 部署 Checklist

### Render 環境變數

```
TELEGRAM_BOT_TOKEN=
OPENROUTER_API_KEY=
APP_ENV=production
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
MEMORY_MAX_MESSAGES=20
TAVILY_API_KEY=
DEFAULT_SEARCH_ENGINE=tavily
SCHEDULER_SECRET=
TELEGRAM_OWNER_CHAT_ID=
RENDER_EXTERNAL_URL=
PORT=10000
```

### GitHub Secrets

```
RENDER_URL=
SCHEDULER_SECRET=
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

### 每次部署後驗證

```bash
# 1. Health check
curl https://your-app.onrender.com/ping
# → {"status": "alive"}

# 2. Telegram webhook 確認
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
# → "url": "https://your-app.onrender.com/webhook"

# 3. MCP 工具列表
curl -X POST https://your-app.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## 版本進度總覽

| 版本 | 功能 | 狀態 |
|------|------|------|
| V0.1 | Telegram + OpenRouter + 21 模型 fallback | ✅ 完成 |
| V0.2 | `/model` 多模型切換 | ✅ 完成 |
| V0.3 | Supabase 對話記憶體 + `/clear` | ✅ 完成 |
| V0.4 | GitHub Actions Keep-Alive + 排程器 | ✅ 完成 |
| V0.5 | News Agent — 每日 AI/Robotics 新聞 | ✅ 完成 |
| V0.6 | Paper Agent — 每日 arXiv 論文摘要 | ✅ 完成 |
| V0.7 | Browser Agent — Tavily + Jina Reader | ✅ 完成 |
| V0.8 | MCP Server — Cline 整合 | ✅ 完成 |
| V0.9 | Robot Tool — ROS2 Bridge Agent | ✅ 完成 |
| V1.0 | Dynamic Model Registry + Multi-Provider | ✅ 完成 |

---

## V1.0 — Dynamic Model Registry + Multi-Provider

### 架構

```
Supabase models 表
  ├── alias       (短名稱，如 gemma / claude / gpt4o)
  ├── model_id    (完整 model string)
  ├── provider    (openrouter / openai / anthropic / google)
  ├── base_url    (各家 API endpoint)
  ├── api_key     (各家 key，空白則用 OPENROUTER_API_KEY)
  ├── priority    (fallback 順序，數字越小越優先)
  └── is_active   (啟用/停用，不刪除直接切換)
```

### Supabase SQL

```sql
CREATE TABLE models (
  id          BIGSERIAL PRIMARY KEY,
  alias       TEXT UNIQUE NOT NULL,
  model_id    TEXT NOT NULL,
  provider    TEXT NOT NULL DEFAULT 'openrouter',
  base_url    TEXT NOT NULL DEFAULT 'https://openrouter.ai/api/v1',
  api_key     TEXT NOT NULL DEFAULT '',
  priority    INT NOT NULL DEFAULT 99,
  is_active   BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO models (alias, model_id, provider, priority) VALUES
  ('gemma',    'google/gemma-4-31b-it:free',                 'openrouter', 1),
  ('gemma3',   'google/gemma-3-27b-it:free',                 'openrouter', 2),
  ('llama',    'meta-llama/llama-4-scout:free',              'openrouter', 3),
  ('qwen',     'qwen/qwen3-coder:free',                      'openrouter', 4),
  ('mistral',  'mistralai/mistral-7b-instruct:free',         'openrouter', 5),
  ('nemotron', 'nvidia/nemotron-3-ultra-550b-a55b:free',     'openrouter', 6),
  ('gpt120',   'openai/gpt-oss-120b:free',                   'openrouter', 7),
  ('hermes',   'nousresearch/hermes-3-llama-3.1-405b:free',  'openrouter', 8),
  ('deepseek', 'deepseek/deepseek-r1',                       'openrouter', 20);
```

### 新增核心檔案

**`src/llm/llm.py`** — 通用 LLM client，從 Supabase 動態載入模型，支援任意 provider

- 啟動時從 DB 載入模型清單並 cache
- 每次 `/model add/remove/on/off` 後呼叫 `invalidate_cache()` 清除 cache
- `chat()` 依 priority 順序嘗試 fallback

**`src/memory/supabase.py`** — 新增 model registry CRUD：
- `db_list_models()` — 列出所有模型
- `db_add_model()` — 新增或更新模型（upsert by alias）
- `db_remove_model()` — 刪除模型
- `db_toggle_model()` — 啟用/停用模型

### Telegram 新增指令

| 指令 | 說明 |
|------|------|
| `/status` | 顯示系統狀態（模型、搜尋引擎、機器人連線、DB 模型數） |
| `/model list` | 從 DB 動態載入模型清單 |
| `/model add <alias> <model_id> <provider> [priority] [base_url] [api_key]` | 新增模型 |
| `/model remove <alias>` | 刪除模型 |
| `/model on <alias>` | 啟用模型 |
| `/model off <alias>` | 停用模型 |

### 新增不同 Provider 範例

```
# OpenAI 直連
/model add gpt4o gpt-4o openai 10 https://api.openai.com/v1 sk-你的key

# Anthropic Claude
/model add claude claude-3-5-sonnet-20241022 anthropic 10 https://api.anthropic.com/v1 sk-ant-你的key

# Google Gemini (via OpenRouter)
/model add gemini google/gemini-2.0-flash:free openrouter 3

# 任何 OpenRouter 新模型
/model add newmodel provider/model-name:free openrouter 5
```

### 驗證

```
/status
→ 📊 Hermes System Status
→ 🤖 Model: auto (fallback)
→ 🔍 Search: tavily
→ 📦 Active models in DB: 9  ✅

/model list
→ 顯示 9 個模型，從 Supabase 動態載入  ✅

/model add testmodel meta-llama/llama-4-scout:free openrouter 1
→ ✅ Model testmodel added/updated

/model off testmodel
→ ⏸ Model testmodel disabled

/model remove testmodel
→ 🗑 Model testmodel removed  ✅
```
