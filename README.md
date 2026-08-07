# Project Hermes-CLOUD

Personal AI Operating System — Agent Runtime built on OpenRouter + Telegram.

## Architecture

```
Telegram
   ↓
Bot (Commands + Messages)
   ↓
Agent Runtime
   ├── LLM (Dynamic Model Registry → Supabase)
   │     └── OpenRouter / OpenAI / Anthropic / NVIDIA NIM
   ├── Memory (Supabase conversations)
   ├── Tools
   │     ├── Browser (Tavily + Google News RSS + Jina Reader)
   │     ├── News Agent (Google News RSS → LLM Summary)
   │     ├── Paper Agent (arXiv → LLM Summary)
   │     ├── Calendar (Supabase calendar table)
   │     ├── Email (SMTP/IMAP)
   │     └── Code Exec (Python subprocess sandbox)
   ├── MCP Server (FastAPI /mcp, Cline integration)
   └── Robot Bridge (WebSocket → WSL2 ROS2 → /cmd_vel)
        ↓
   Scheduler (GitHub Actions)
        ├── Keep-Alive (every 14 min)
        ├── News (daily 08:00 UTC+8)
        ├── Paper (daily 08:30 UTC+8)
        ├── Calendar Reminder (daily 08:00 UTC+8)
        └── Proactive Agent (07:30 / 08:00 / 19:00 UTC+8)
```

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| V0.1 | Telegram + OpenRouter | ✅ |
| V0.2 | Multi-model switching | ✅ |
| V0.3 | Supabase Memory | ✅ |
| V0.4 | GitHub Actions Scheduler | ✅ |
| V0.5 | News Agent | ✅ |
| V0.6 | Paper Agent | ✅ |
| V0.7 | Browser Agent | ✅ |
| V0.8 | MCP Server | ✅ |
| V0.9 | Robot Tool (ROS2 Bridge) | ✅ |
| V1.0 | Dynamic Model Registry + Multi-Provider | ✅ |
| V1.1 | Calendar + Email + Code Execution Tools | ✅ |
| V1.2 | Calendar Reminder (daily push notification) | ✅ |
| V1.3 | Memory Auto-Summarise (LLM compression) | ✅ |
| V1.4 | Voice Input (Whisper transcription) | ✅ |
| V1.5 | Image Input (Vision model analysis) | ✅ |
| V1.6 | Todo List (Supabase todos table) | ✅ |
| V1.7 | Proactive Agent (scheduled push notifications) | ✅ |

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Show help |
| `/status` | System status (model, search, robot, DB) |
| `/model list` | List all models from DB |
| `/model <alias>` | Switch to specific model |
| `/model auto` | Switch back to auto fallback mode |
| `/model add <alias> <model_id> <provider> [priority] [base_url] [api_key]` | Add/update model |
| `/model remove <alias>` | Delete model |
| `/model on <alias>` | Enable model |
| `/model off <alias>` | Disable model |
| `/search list` | List search engines |
| `/search <engine>` | Switch search engine (tavily / news) |
| `/browse <url>` | Fetch and summarize a webpage |
| `/browse <keywords>` | Force web search |
| `/todo list` | List pending todos |
| `/todo all` | List all todos (including done) |
| `/todo add <title>` | Add todo item |
| `/todo done <title>` | Mark todo as done |
| `/todo del <title>` | Delete todo item |
| `/calendar list [days]` | List upcoming events |
| `/calendar add <title> <date>` | Add calendar event |
| `/calendar del <title>` | Delete calendar event |
| `/email inbox [count]` | Read inbox emails |
| `/email send <to> <subject> \| <body>` | Send email |
| `/run <python code>` | Execute Python code |
| `/clear` | Clear conversation memory |

## Local Setup

```bash
cp .env.example .env
# Fill in your keys in .env

pip install -r requirements.txt
python main.py
```

## Project Structure

```
src/
  telegram/    # Telegram Bot + command handlers
  llm/         # Universal LLM client (multi-provider)
  agent/       # Agent Runtime + Session
  memory/      # Supabase (conversations + model registry)
  tools/       # Browser / News / Paper / Calendar / Email / Code Exec
  mcp/         # MCP Server (FastAPI)
bridge/        # ROS2 Bridge Agent (WSL2 local)
config/        # Settings
docker/        # Dockerfile for Render
.github/       # GitHub Actions workflows
docs/          # SOP documentation
```

## Deployment

- **Cloud**: Render Free tier (`https://hermes-cloud-y1i2.onrender.com`)
- **Webhook**: Auto-set on startup via `RENDER_EXTERNAL_URL`
- **Keep-Alive**: GitHub Actions pings every 14 min
- **Robot Bridge**: Run `bridge/bridge_agent.py` locally in WSL2
