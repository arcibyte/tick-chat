import asyncio
import httpx

from app.config import CENTRAL_URL, GROUP_NAME, PUBLIC_URL, logger
from app.database import get_pending_messages, mark_message_synced
from app.schemas import FederatedMessage

central_online = True
consecutive_failures = 0


async def register_with_central(client: httpx.AsyncClient):
    payload = {"server": GROUP_NAME, "url": PUBLIC_URL}
    try:
        resp = await client.post(f"{CENTRAL_URL}/register", json=payload, timeout=5.0)
        if 200 <= resp.status_code < 300:
            logger.info(f"REGISTER_OK server={GROUP_NAME} url={PUBLIC_URL}")
        else:
            logger.warning(f"REGISTER_FAIL status={resp.status_code} body={resp.text}")
    except Exception as exc:
        logger.warning(f"REGISTER_ERROR error={exc}")


async def send_with_backoff(client: httpx.AsyncClient, msg: FederatedMessage):
    global central_online
    attempt = 0
    backoff = 1.0
    payload = msg.model_dump(by_alias=True)

    while True:
        if not central_online:
            logger.info(f"QUEUED_OFFLINE id={msg.id} lamport={msg.lamport}")
            return

        attempt += 1
        try:
            resp = await client.post(f"{CENTRAL_URL}/messages", json=payload, timeout=5.0)
            if 200 <= resp.status_code < 300:
                mark_message_synced(msg.id, 1)
                logger.info(f"SEND_OK id={msg.id} lamport={msg.lamport} attempt={attempt}")
                return
            elif 400 <= resp.status_code < 500:
                mark_message_synced(msg.id, -1)
                logger.error(f"SEND_ABORT_4XX id={msg.id} status={resp.status_code} body={resp.text}")
                return
            else:
                logger.warning(
                    f"SEND_RETRY_5XX id={msg.id} status={resp.status_code} attempt={attempt} wait={backoff}s"
                )
        except Exception as exc:
            logger.warning(
                f"SEND_RETRY_NET id={msg.id} attempt={attempt} wait={backoff}s error={exc}"
            )

        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30.0)


async def flush_pending_messages(client: httpx.AsyncClient):
    pending = get_pending_messages()
    if pending:
        logger.info(f"FLUSH_START count={len(pending)}")
        for msg in pending:
            if not central_online:
                break
            await send_with_backoff(client, msg)


async def background_supervisor():
    while True:
        await asyncio.sleep(3600)
