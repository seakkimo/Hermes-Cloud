# Hermes Telegram Command Reference

## 一般對話

直接輸入文字即可與 AI 對話，無需指令。
Calendar、Email、Code Exec 也支援自然語言，不一定要下指令。

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
Current: `auto`

*[nvidia]*
  ✅ `glm-nv`        → `z-ai/glm-5.2`                        (p:20)
  ✅ `kimi-nv`       → `moonshotai/kimi-k2.6`                 (p:20)
  ✅ `nemotron-nv`   → `nvidia/nemotron-3-ultra-550b-a55b`    (p:20)

*[openrouter]*
  ✅ `gemma`         → `google/gemma-4-31b-it:free`           (p:1)
  ✅ `kimi`          → `moonshotai/kimi-k2.6`                 (p:10)
  ⏸ `mistral`       → `mistralai/mistral-7b-instruct:free`   (p:50)
```

### 切換至指定模型

```
/model <alias>
```

範例：
```
/model kimi        ← 用 OpenRouter API
/model kimi-nv     ← 用 NVIDIA NIM API（同模型，不同供應商）
/model gemma
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
| alias | 是 | 自訂短名稱（小寫），nvidia 模型建議加 `-nv` 後綴 |
| model_id | 是 | 完整 model ID |
| provider | 是 | `openrouter` / `openai` / `anthropic` / `nvidia` |
| priority | 否 | 數字越小越優先，預設 50 |
| base_url | 否 | 自訂 API endpoint，預設 OpenRouter |
| api_key | 否 | 自訂 API Key，預設使用環境變數 |

範例：
```
/model add gemini google/gemini-2.0-flash-exp:free openrouter 1
/model add claude claude-3-5-sonnet-20241022 anthropic 10 https://api.anthropic.com/v1 sk-ant-xxx
/model add gpt4o gpt-4o openai 10 https://api.openai.com/v1 sk-xxx
/model add llama-nv meta/llama-3.1-70b-instruct nvidia 20 https://integrate.api.nvidia.com/v1 nvapi-xxx
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

### 測試模型

```
/model test <alias>
```

發送一個最小 prompt 測試模型可用性，回傳延遲時間和狀態。

輸出範例：
```
✅ Model Test: `gemma`
Model: `google/gemma-4-31b-it:free`
Provider: `openrouter`
Status: `ok`
Latency: `1243 ms`
Reply: `OK`
```

狀態說明：
| Status | 說明 |
|--------|------|
| `ok` | 模型可用 |
| `rate_limited` | 設到限流（429） |
| `not_found_api` | 模型 ID 不存在（404） |
| `error` | 其他錯誤 |

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
每天 08:00 自動推送未來 24 小時內的事件提醒。
詳細說明：`docs/V1.1_FEATURES.md`

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
/calendar add <title> <YYYY-MM-DD>
/calendar add <title> <YYYY-MM-DD HH:MM>
```

範例：
```
/calendar add 牙醫回診 2025-07-25
/calendar add 週會 2025-07-21 10:00
```

### 刪除事件（模糊比對標題）

```
/calendar del <title>
```

範例：
```
/calendar del 牙醫
/calendar del 週會
```

### 自然語言用法（不需下指令）

```
幫我記一下，7月25號要去看牙醫
下週一早上10點有個會議，幫我加進行事曆
我這週有什麼行程？
把牙醫的行程刪掉
```

---

## /email — 電子郵件（V1.1）

> 需在 Render 環境變數設定 `EMAIL_ADDRESS`、`EMAIL_PASSWORD`（Gmail 請使用 App Password）
> 詳細說明：`docs/V1.1_FEATURES.md`

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

輸出範例：
```
[1] Mon, 14 Jul 2025
    From: sender@gmail.com
    Subject: 會議通知
[2] Sun, 13 Jul 2025
    From: news@example.com
    Subject: 每週電子報
```

### 讀取完整內文

```
/email read <no>
```

| 參數 | 說明 |
|------|------|
| no | inbox 列表的序號，1 = 最新一封 |

範例：
```
/email read 1     ← 讀最新一封的完整內文
/email read 3     ← 讀第 3 封的完整內文
```

### 發送郵件

```
/email send <to> <subject> | <body>
```

> 主旨與內文之間用 `|` 分隔

範例：
```
/email send friend@gmail.com 你好 | 這是 Hermes 發的測試信！
/email send boss@company.com 請假申請 | 您好，我明天需要請假一天，謝謝。
```

### 自然語言用法（不需下指令）

```
幫我寄信給 friend@gmail.com，主旨「週末聚餐」，說週六晚上7點見
查一下我的信箱有沒有新郵件
讀最新10封信給我看
```

---

## /run — Python 程式執行（V1.1）

在沙盒環境執行 Python 程式碼，timeout 10 秒，輸出上限 2000 字元。
詳細說明：`docs/V1.1_FEATURES.md`

```
/run <python code>
```

範例：
```
/run print(sum(range(1, 101)))
/run import math; print(math.sqrt(144))
/run from datetime import datetime; print(datetime.now())
/run import json; print(json.dumps({'name':'Hermes','v':1.1}, indent=2))
```

### 自然語言用法（不需下指令）

```
幫我算 1 到 1000 的總和
用 Python 算費波那契數列前 10 項
現在幾點？用 Python 顯示台灣時間
```

---

## 注意事項

- `/model add` 若 alias 已存在則為更新（upsert）
- `/model auto` 會依 priority 排序自動 fallback，跳過不支援 function calling 的模型
- 不支援 function calling 的模型（nemotron、hermes、dolphin、mistral-7b 等）會自動改用關鍵字路由
- nvidia provider 的 alias 建議加 `-nv` 後綴，方便與 openrouter 同名模型區分
- `/email` 需設定 Gmail App Password（16位），非帳號密碼，申請：myaccount.google.com/apppasswords
- `/run` 有 10 秒 timeout 保護，不能安裝額外套件，不能存取檔案系統
- Robot Bridge 需在 WSL2 本地端啟動 `bridge/bridge_agent.py`，每次 Render redeploy 後需重啟（建議用 `nohup` 背景執行）
