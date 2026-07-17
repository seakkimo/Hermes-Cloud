import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, OPENROUTER_BASE_URL
from src.agent.runtime import run
from src.agent.session import get_model, set_model, AUTO_MODEL, get_search_engine, set_search_engine
from src.memory.supabase import clear_history, db_list_models, db_add_model, db_remove_model, db_toggle_model
from src.llm.llm import invalidate_cache, list_models
from src.tools.browser import SEARCH_ENGINES

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Hermes V1.0 online.*\n\n"
        "*模型管理*\n"
        "`/model list` — 列出所有模型\n"
        "`/model <alias>` — 切換模型\n"
        "`/model auto` — 自動 fallback 模式\n"
        "`/model add <alias> <model_id> <provider> [priority]` — 新增模型\n"
        "`/model remove <alias>` — 刪除模型\n"
        "`/model on <alias>` — 啟用模型\n"
        "`/model off <alias>` — 停用模型\n\n"
        "*搜尋*\n"
        "`/search list` — 列出搜尋引擎\n"
        "`/search <engine>` — 切換搜尋引擎\n"
        "`/browse <url|keywords>` — 搜尋或擷取網頁\n\n"
        "*其他*\n"
        "`/status` — 系統狀態\n"
        "`/clear` — 清除對話記憶",
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    model = get_model(user_id)
    engine = get_search_engine(user_id)
    models = await list_models(all_models=True)

    # Check robot bridge
    try:
        import httpx
        from config.settings import RENDER_EXTERNAL_URL
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{RENDER_EXTERNAL_URL}/ws/robot/status")
            robot = "🟢 connected" if r.json().get("connected") else "🔴 disconnected"
    except Exception:
        robot = "❓ unknown"

    active = len([m for m in models if m['is_active']])
    lines = [
        "📊 *Hermes System Status*\n",
        f"🤖 Model: `{model_display}`",
        f"🔍 Search: `{engine}`",
        f"🦾 Robot: {robot}",
        f"📦 Models in DB: `{active}` active / `{len(models)}` total",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    args = context.args

    # /model list
    if not args or args[0] == "list":
        models = await list_models(all_models=True)
        current = get_model(user_id)
        display = "auto" if current == AUTO_MODEL else current
        lines = [f"Current: `{display}`\n", "Available models:"]
        for m in models:
            status = "✅" if m["is_active"] else "⏸"
            lines.append(f"  {status} `{m['alias']}` → `{m['model_id']}` [{m['provider']}] (priority:{m['priority']})") 
        lines.append("\n`/model auto` to reset to fallback mode")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    sub = args[0].lower()

    # /model auto
    if sub == "auto":
        set_model(user_id, AUTO_MODEL)
        await update.message.reply_text("✅ Switched to auto fallback mode.")
        return

    # /model add <alias> <model_id> <provider> [priority] [base_url] [api_key]
    if sub == "add":
        if len(args) < 4:
            await update.message.reply_text(
                "Usage: `/model add <alias> <model_id> <provider> [priority] [base_url] [api_key]`\n\n"
                "Examples:\n"
                "`/model add claude claude-3-5-sonnet-20241022 anthropic 10 https://api.anthropic.com/v1 sk-ant-xxx`\n"
                "`/model add gpt4o gpt-4o openai 10 https://api.openai.com/v1 sk-xxx`\n"
                "`/model add gemini gemini-2.0-flash openrouter 5`",
                parse_mode="Markdown"
            )
            return
        alias = args[1].lower()
        model_id = args[2]
        provider = args[3].lower()
        priority = int(args[4]) if len(args) > 4 else 50
        base_url = args[5] if len(args) > 5 else OPENROUTER_BASE_URL
        api_key = args[6] if len(args) > 6 else ""
        await db_add_model(alias, model_id, provider, base_url, api_key, priority)
        invalidate_cache()
        await update.message.reply_text(f"✅ Model `{alias}` added/updated.", parse_mode="Markdown")
        return

    # /model remove <alias>
    if sub == "remove":
        if len(args) < 2:
            await update.message.reply_text("Usage: `/model remove <alias>`", parse_mode="Markdown")
            return
        alias = args[1].lower()
        await db_remove_model(alias)
        invalidate_cache()
        await update.message.reply_text(f"🗑 Model `{alias}` removed.", parse_mode="Markdown")
        return

    # /model on <alias>
    if sub == "on":
        if len(args) < 2:
            await update.message.reply_text("Usage: `/model on <alias>`", parse_mode="Markdown")
            return
        alias = args[1].lower()
        await db_toggle_model(alias, True)
        invalidate_cache()
        await update.message.reply_text(f"✅ Model `{alias}` enabled.", parse_mode="Markdown")
        return

    # /model off <alias>
    if sub == "off":
        if len(args) < 2:
            await update.message.reply_text("Usage: `/model off <alias>`", parse_mode="Markdown")
            return
        alias = args[1].lower()
        await db_toggle_model(alias, False)
        invalidate_cache()
        await update.message.reply_text(f"⏸ Model `{alias}` disabled.", parse_mode="Markdown")
        return

    # /model <alias> — switch to specific model
    models = await list_models()
    aliases = [m["alias"] for m in models]
    if sub not in aliases:
        await update.message.reply_text(
            f"❌ Unknown alias `{sub}`. Use `/model list` to see options.",
            parse_mode="Markdown"
        )
        return
    set_model(user_id, sub)
    model_row = next(m for m in models if m["alias"] == sub)
    await update.message.reply_text(
        f"✅ Switched to `{model_row['model_id']}` [{model_row['provider']}]\n"
        f"⚠️ Use `/model auto` to re-enable fallback.",
        parse_mode="Markdown"
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    args = context.args
    if not args or args[0] == "list":
        current = get_search_engine(user_id)
        lines = [f"Current engine: `{current}`\n", "Available engines:"]
        lines += [f"  `{e}`" for e in SEARCH_ENGINES]
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    engine = args[0].lower()
    if engine not in SEARCH_ENGINES:
        await update.message.reply_text(
            f"❌ Unknown engine `{engine}`. Available: {', '.join(SEARCH_ENGINES)}",
            parse_mode="Markdown"
        )
        return
    set_search_engine(user_id, engine)
    await update.message.reply_text(f"✅ Search engine switched to `{engine}`", parse_mode="Markdown")


async def browse_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Usage:\n`/browse <url>` — fetch a webpage\n`/browse <keywords>` — search the web",
            parse_mode="Markdown"
        )
        return
    query = " ".join(context.args)
    user_id = update.effective_user.id
    await update.message.chat.send_action("typing")
    is_url = query.startswith("http://") or query.startswith("https://")
    try:
        if is_url:
            reply = await run(f"請摘要這個網頁的主要內容：{query}", user_id=user_id, force_browse=query)
        else:
            reply = await run(query, user_id=user_id, force_search=True)
        if not reply:
            reply = "⚠️ 無法取得內容。"
    except Exception as e:
        logger.error(f"Browse error: {e}")
        reply = "⚠️ 發生錯誤，請稍後再試。"
    await update.message.reply_text(reply)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await clear_history(update.effective_user.id)
    await update.message.reply_text("🧹 Conversation history cleared.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text
    logger.info(f"Received message from {user_id}")
    await update.message.chat.send_action("typing")
    try:
        reply = await run(user_text, user_id=user_id)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = "⚠️ All models are currently unavailable. Please try again in a moment."
    await update.message.reply_text(reply)


def build_app():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("browse", browse_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
