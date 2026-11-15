from fastapi import APIRouter, Response

from app.config import GROUP_NAME, db_lock, logger
from app.database import get_lamport, save_incoming_message
from app.schemas import FederatedMessage

router = APIRouter(prefix="/fed", tags=["federation"])


@router.get("/health")
async def fed_health():
    return {"server": GROUP_NAME, "lamport": get_lamport()}


@router.post("/messages")
async def fed_receive_message(msg: FederatedMessage, response: Response):
    async with db_lock:
        is_new = save_incoming_message(msg)
        if not is_new:
            logger.info(f"DEDUP_DISCARD id={msg.id} from={msg.from_} lamport={msg.lamport}")
    response.status_code = 200
    return {"status": "ok", "id": msg.id}
