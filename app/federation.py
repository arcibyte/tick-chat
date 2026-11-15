import asyncio
import httpx

from app.config import (
    CENTRAL_URL,
    GROUP_NAME,
    HEARTBEAT_INTERVAL,
    MAX_HEALTH_FAILURES,
    PUBLIC_URL,
    REGISTER_INTERVAL,
    db_lock,
    logger,
)
from app.database import (
    get_max_synced_lamport,
    get_pending_messages,
    mark_message_synced,
    save_incoming_message,
)
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


async def recover_history(client: httpx.AsyncClient):
    since_lamport = get_max_synced_lamport()
    try:
        resp = await client.get(
            f"{CENTRAL_URL}/history", params={"since": since_lamport}, timeout=5.0
        )
        if 200 <= resp.status_code < 300:
            data = resp.json()
            messages_list = data if isinstance(data, list) else data.get("messages", [])
            recovered = 0
            async with db_lock:
                for raw_msg in messages_list:
                    msg = FederatedMessage.model_validate(raw_msg)
                    if save_incoming_message(msg):
                        recovered += 1
            logger.info(
                f"HISTORY_SYNC since={since_lamport} fetched={len(messages_list)} new_applied={recovered}"
            )
    except Exception as exc:
        logger.warning(f"HISTORY_SYNC_ERROR since={since_lamport} error={exc}")


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
    global central_online, consecutive_failures
    last_register = 0.0

    async with httpx.AsyncClient() as client:
        await register_with_central(client)
        await recover_history(client)
        await flush_pending_messages(client)

        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                resp = await client.get(f"{CENTRAL_URL}/health", timeout=3.0)
                if 200 <= resp.status_code < 300:
                    if not central_online:
                        logger.info("CENTRAL_RECOVERED ejecutando re-registro y sincronizacion")
                        central_online = True
                        consecutive_failures = 0
                        await register_with_central(client)
                        await recover_history(client)
                        await flush_pending_messages(client)
                    else:
                        consecutive_failures = 0
                else:
                    raise RuntimeError(f"Status {resp.status_code}")
            except Exception as exc:
                consecutive_failures += 1
                logger.warning(
                    f"HEARTBEAT_FAIL count={consecutive_failures}/{MAX_HEALTH_FAILURES} error={exc}"
                )
                if consecutive_failures >= MAX_HEALTH_FAILURES and central_online:
                    central_online = False
                    logger.error("CENTRAL_MARKED_DOWN guardando mensajes en cola local")

            now = asyncio.get_event_loop().time()
            if central_online and (now - last_register >= REGISTER_INTERVAL):
                await register_with_central(client)
                last_register = now
