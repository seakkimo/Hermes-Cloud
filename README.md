# Project Hermes-CLOUD

Personal AI Operating System — Agent Runtime built on OpenRouter + Telegram.

## Architecture

```
Telegram → Bot → Agent Runtime → OpenRouter → DeepSeek / Qwen / Gemini / Claude
                      ↓
                 Memory (Supabase)
                 Scheduler (GitHub Actions)
                 Tools (Browser, GitHub, MCP)
```

## Roadmap

| Version | Feature |
|---------|---------|
| V0.1 | Telegram + OpenRouter |
| V0.2 | Multi-model switching |
| V0.3 | Supabase Memory |
| V0.4 | GitHub Actions Scheduler |
| V0.5 | News Agent |
| V0.6 | Paper Agent |
| V0.7 | Browser Agent |
| V0.8 | MCP |
| V0.9 | Robot Tool |
| V1.0 | Personal AI Operating System |

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
  telegram/    # Telegram Bot plugin
  llm/         # LLM call layer (OpenRouter)
  agent/       # Agent Runtime / Orchestrator
  memory/      # Memory plugin (Supabase, future)
  scheduler/   # Scheduler plugin (future)
  tools/       # Tool plugins (future)
config/        # Unified settings
docker/        # Dockerfile for Render
tests/         # Tests
docs/          # Documentation
```
