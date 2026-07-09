import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN
from src.agent.runtime import run

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hermes online. Send me a message to begin."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    logger.info(f"Received message from {update.effective_user.id}")

    await update.message.chat.send_action("typing")
    try:
        reply = await run(user_text)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = "⚠️ All models are currently unavailable. Please try again in a moment."
    await update.message.reply_text(reply)


def build_app():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
