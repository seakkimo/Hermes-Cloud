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
  ✅ gemini    → google/gemini-2.0-flash-exp:free  (priority:1)
  ✅ deepseek  → deepseek/deepseek-r1:free          (priority:2)
  ⏸ nemotron  → nvidia/llama-3.1-nemotron-70b:free (priority:5)

[anthropic]
  ✅ claude    → claude-3-5-sonnet-20241022         (priority:10)

[openai]
  ✅ gpt4o     → gpt-4o                             (priority:10)
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
| alias | ✅ | 自訂短名稱（小寫） |
| model_id | ✅ | 完整 model ID |
| provider | ✅ | `openrouter` / `openai` / `anthropic` |
| priority | ❌ | 數字越小越優先，預設 50 |
| base_url | ❌ | 自訂 API endpoint，預設 OpenRouter |
| api_key | ❌ | 自訂 API Key，預設使用環境變數 |

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

範例：
```
/model remove nemotron
```

### 啟用 / 停用模型

```
/model on <alias>
/model off <alias>
```

範例：
```
/model on deepseek
/model off nemotron
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

可用引擎：
| engine | 說明 |
|--------|------|
| `tavily` | Tavily AI Search（預設） |
| `news` | Google News RSS |

範例：
```
/search tavily
/search news
```

---

## /browse — 網頁擷取 / 搜尋

### 擷取並摘要網頁

```
/browse <url>
```

範例：
```
/browse https://openai.com/blog/gpt-4o
```

### 強制網路搜尋

```
/browse <keywords>
```

範例：
```
/browse latest AI news 2025
/browse Taiwan earthquake today
```

---

## 注意事項

- `/model add` 若 alias 已存在則為更新（upsert）
- `/model auto` 會依 priority 排序自動 fallback，跳過不支援 function calling 的模型
- 不支援 function calling 的模型（nemotron、hermes、dolphin、mistral-7b 等）會自動改用關鍵字路由
- Robot Bridge 需在 WSL2 本地端啟動 `bridge/bridge_agent.py`，每次 Render redeploy 後需重啟
