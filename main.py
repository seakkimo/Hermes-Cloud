import logging
from config.settings import LOG_LEVEL
from src.telegram.bot import build_app

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)

if __name__ == "__main__":
    app = build_app()
    app.run_polling()
