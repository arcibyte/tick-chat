import asyncio
import logging
import os

GROUP_NAME = os.getenv("GROUP_NAME", "g1")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")
CENTRAL_URL = os.getenv("CENTRAL_URL", "http://localhost:9000")
DB_PATH = os.getenv("DB_PATH", "./data/tickchat.db")
MAX_HEALTH_FAILURES = int(os.getenv("MAX_HEALTH_FAILURES", "3"))
HEARTBEAT_INTERVAL = float(os.getenv("HEARTBEAT_INTERVAL", "5.0"))
REGISTER_INTERVAL = float(os.getenv("REGISTER_INTERVAL", "30.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [tick-chat:%(name)s] %(message)s",
)
logger = logging.getLogger(GROUP_NAME)

db_lock = asyncio.Lock()
