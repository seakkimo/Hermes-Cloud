import logging
import uvicorn
from fastapi import FastAPI, Request, Header, HTTPException
from telegram import Update
from config.settings import LOG_LEVEL, APP_ENV, RENDER_EXTERNAL_URL, PORT, SCHEDULER_SECRET
from src.telegram.bot import build_app

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)

logger = logging.getLogger(__name__)


def run_polling():
    app = build_app()
    logger.info("Starting in polling mode (local)")
    app.run_polling()


def run_webhook():
    tg_app = build_app()
    web = FastAPI()

    @web.get("/health")
    async def health():
        return {"status": "ok"}

    @web.get("/ping")
    async def ping():
        logger.info("Keep-alive ping received")
        return {"status": "alive"}

    @web.post("/task")
    async def task(request: Request, x_scheduler_secret: str = Header(default="")):
        if x_scheduler_secret != SCHEDULER_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")
        data = await request.json()
        task_name = data.get("task")
        logger.info(f"Scheduler task received: {task_name}")
        # Future: route to task handlers
        return {"status": "received", "task": task_name}

    @web.post("/webhook")
    async def webhook(request: Request):
        data = await request.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
        return {"ok": True}

    async def startup():
        await tg_app.initialize()
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await tg_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to {webhook_url}")

    async def shutdown():
        await tg_app.shutdown()

    web.add_event_handler("startup", startup)
    web.add_event_handler("shutdown", shutdown)

    logger.info(f"Starting in webhook mode on port {PORT}")
    uvicorn.run(web, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    if APP_ENV == "production":
        run_webhook()
    else:
        run_polling()
