import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, MODEL_ALIASES
from src.agent.runtime import run
from src.agent.session import get_model, set_model, AUTO_MODEL
from src.memory.supabase import clear_history

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hermes online. Send me a message to begin.\n"
        "Use /model list to see available models.\n"
        "Use /model <name> to switch models.\n"
        "Use /clear to clear conversation memory.\n"
        "Use /browse <url> to fetch a webpage."
    )


async def browse_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "`/browse <url>` — fetch a webpage\n"
            "`/browse <keywords>` — search the web",
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
            # Treat as search query
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


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    args = context.args

    if not args or args[0] == "list":
        current = get_model(user_id)
        display = "auto (fallback)" if current == AUTO_MODEL else current
        lines = [f"Current model: `{display}`\n", "Available aliases:"]
        lines += [f"  `{alias}` → `{model_id}`" for alias, model_id in MODEL_ALIASES.items()]
        lines.append("\nUse `/model auto` to switch back to auto fallback mode.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    alias = args[0].lower()

    if alias == "auto":
        set_model(user_id, AUTO_MODEL)
        await update.message.reply_text("✅ Switched to auto mode. System will fallback automatically.") 
        return

    if alias not in MODEL_ALIASES:
        await update.message.reply_text(
            f"❌ Unknown model `{alias}`. Use /model list to see options.",
            parse_mode="Markdown"
        )
        return

    model_id = MODEL_ALIASES[alias]
    set_model(user_id, model_id)
    await update.message.reply_text(
        f"✅ Switched to `{model_id}`\n⚠️ If this model is unavailable, use `/model auto` to re-enable fallback.",
        parse_mode="Markdown"
    )


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
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("browse", browse_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
