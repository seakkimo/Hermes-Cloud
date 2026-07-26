# Hermes Telegram Command Reference

## 一般對話

直接輸入文字即可與 AI 對話，無需指令。

---

## /start

顯示指令說明。

```
/start
```

---

## /status

顯示系統目前狀態，包含：當前模型、搜尋引擎、Robot Bridge 連線狀態、DB 模型數量。

```
/status
```

---

## /clear

清除目前使用者的對話記憶（Supabase conversations）。

```
/clear
```

---

## /model — 模型管理

### 列出所有模型（按 provider 分組）

```
/model list
```

輸出範例：
```
Current: auto

[openrouter]
  ✅ gemini   → google/gemini-2.0-flash-exp:free  (p:1)
  ✅ deepseek → deepseek/deepseek-r1:free          (p:2)
  ⏸ nemotron → nvidia/llama-3.1-nemotron-70b:free (p:5)

[anthropic]
  ✅ claude   → claude-3-5-sonnet-20241022         (p:10)

[openai]
  ✅ gpt4o    → gpt-4o                             (p:10)
```

### 切換至指定模型

```
/model <alias>
```

範例：
```
/model gemini
/model claude
```

### 切換回自動 fallback 模式

```
/model auto
```

### 新增 / 更新模型

```
/model add <alias> <model_id> <provider> [priority] [base_url] [api_key]
```

| 參數 | 必填 | 說明 |
|------|------|------|
| alias | 是 | 自訂短名稱（小寫） |
| model_id | 是 | 完整 model ID |
| provider | 是 | `openrouter` / `openai` / `anthropic` |
| priority | 否 | 數字越小越優先，預設 50 |
| base_url | 否 | 自訂 API endpoint，預設 OpenRouter |
| api_key | 否 | 自訂 API Key，預設使用環境變數 |

範例：
```
/model add gemini google/gemini-2.0-flash-exp:free openrouter 1
/model add claude claude-3-5-sonnet-20241022 anthropic 10 https://api.anthropic.com/v1 sk-ant-xxx
/model add gpt4o gpt-4o openai 10 https://api.openai.com/v1 sk-xxx
```

### 刪除模型

```
/model remove <alias>
```

### 啟用 / 停用模型

```
/model on <alias>
/model off <alias>
```

---

## /search — 搜尋引擎管理

### 列出可用搜尋引擎

```
/search list
```

### 切換搜尋引擎

```
/search <engine>
```

| engine | 說明 |
|--------|------|
| `tavily` | Tavily AI Search（預設） |
| `news` | Google News RSS |

---

## /browse — 網頁擷取 / 搜尋

```
/browse <url>          # 擷取並摘要網頁
/browse <keywords>     # 強制網路搜尋
```

範例：
```
/browse https://openai.com/blog/gpt-4o
/browse latest AI news 2025
```

---

## /calendar — 行事曆（V1.1）

事件儲存於 Supabase `calendar` table，依使用者 ID 隔離。

### 列出近期事件

```
/calendar list [days]
```

| 參數 | 說明 |
|------|------|
| days | 往後幾天，預設 7 |

範例：
```
/calendar list
/calendar list 30
```

### 新增事件

```
/calendar add <title> <YYYY-MM-DD HH:MM>
/calendar add <title> <YYYY-MM-DD>
```

範例：
```
/calendar add Team Meeting 2025-07-20 10:00
/calendar add Doctor Appointment 2025-07-25
```

### 刪除事件

```
/calendar del <title>
```

範例：
```
/calendar del Team Meeting
```

---

## /email — 電子郵件（V1.1）

> 需在環境變數設定 `EMAIL_ADDRESS`、`EMAIL_PASSWORD`（Gmail 請使用 App Password）

### 讀取收件匣

```
/email inbox [count]
```

| 參數 | 說明 |
|------|------|
| count | 讀取幾封，預設 5 |

範例：
```
/email inbox
/email inbox 10
```

### 發送郵件

```
/email send <to> <subject> | <body>
```

範例：
```
/email send friend@gmail.com Hello | Hi, this is Hermes!
```

---

## /run — Python 程式執行（V1.1）

在沙盒環境執行 Python 程式碼，timeout 10 秒。

```
/run <python code>
```

範例：
```
/run print(sum(range(100)))
/run import math; print(math.pi)
/run print(2 ** 10)
```

---

## 注意事項

- `/model add` 若 alias 已存在則為更新（upsert）
- `/model auto` 會依 priority 排序自動 fallback，跳過不支援 function calling 的模型
- 不支援 function calling 的模型（nemotron、hermes、dolphin、mistral-7b 等）會自動改用關鍵字路由
- `/email` 需設定 Gmail App Password，非帳號密碼
- `/run` 有 10 秒 timeout 保護，禁止無限迴圈
- Robot Bridge 需在 WSL2 本地端啟動 `bridge/bridge_agent.py`，每次 Render redeploy 後需重啟
