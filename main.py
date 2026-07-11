import logging
import json
import asyncio
import uvicorn
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
from telegram import Update
from config.settings import LOG_LEVEL, APP_ENV, RENDER_EXTERNAL_URL, PORT, SCHEDULER_SECRET, TELEGRAM_OWNER_CHAT_ID
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

    # MCP Server
    from src.mcp.registry import list_tools, call_tool
    from src.mcp import tools as mcp_tools
    mcp_tools.setup()

    async def _handle_mcp_body(body: dict) -> dict:
        req_id = body.get("id")
        method = body.get("method")

        def ok(result):
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        def err(code, message):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

        if method == "initialize":
            return ok({
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hermes", "version": "0.8.0"},
            })

        if method in ("notifications/initialized", "ping"):
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "tools/list":
            return ok({"tools": list_tools()})

        if method == "tools/call":
            name = body.get("params", {}).get("name")
            arguments = body.get("params", {}).get("arguments", {})
            try:
                result = await call_tool(name, arguments)
                return ok({"content": [{"type": "text", "text": str(result)}]})
            except Exception as e:
                return err(-32000, str(e))

        return err(-32601, f"Method not found: {method}")

    @web.get("/mcp")
    async def mcp_sse(request: Request):
        """SSE endpoint for Cline streamable-http transport"""
        async def event_stream():
            # Send endpoint event so client knows where to POST
            yield f"event: endpoint\ndata: /mcp\n\n"
            # Keep alive
            while True:
                if await request.is_disconnected():
                    break
                yield ": keep-alive\n\n"
                await asyncio.sleep(15)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @web.post("/mcp")
    async def mcp_endpoint(request: Request):
        body = await request.json()
        return await _handle_mcp_body(body)

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

        if task_name == "news":
            from src.tools.news import run as news_run
            summary = await news_run()
            await tg_app.bot.send_message(
                chat_id=TELEGRAM_OWNER_CHAT_ID,
                text=summary,
                parse_mode="Markdown",
            )

        elif task_name == "paper":
            from src.tools.paper import run as paper_run
            try:
                summary = await paper_run()
                await tg_app.bot.send_message(
                    chat_id=TELEGRAM_OWNER_CHAT_ID,
                    text=summary,
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Paper task error: {e}")

        return {"status": "ok", "task": task_name}

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
