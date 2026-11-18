from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import GROUP_NAME
from app.database import (
    create_local_user,
    get_history,
    get_local_users,
    increment_lamport,
    save_incoming_message,
)
from app.schemas import FederatedMessage

router = APIRouter(tags=["Local API"])


class UserRequest(BaseModel):
    username: str


class MessageSendRequest(BaseModel):
    from_user: str
    body: str


@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRequest):
    """Crea un usuario local (ej: ana@g1) o permite el acceso si ya existe."""
    username = payload.username.strip()
    if not username or "@" not in username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formato debe ser usuario@grupo (ej: ana@g1).",
        )

    existing_users = get_local_users()
    if username in existing_users:
        return {"message": f"Bienvenido de nuevo, {username}."}

    success = create_local_user(username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo registrar el usuario.",
        )
    return {"message": f"Usuario {username} creado con éxito."}


@router.get("/users")
def list_users():
    """Lista todos los usuarios locales del grupo."""
    return {"users": get_local_users()}


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def send_local_message(payload: MessageSendRequest):
    """
    Permite a un usuario local enviar un mensaje a la sala global #general.
    Incrementa el reloj de Lamport, genera un UUID y lo guarda localmente.
    """
    users = get_local_users()
    if payload.from_user not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El remitente no es un usuario local registrado en este servidor.",
        )

    parts = payload.from_user.split("@")
    origin = parts[1] if len(parts) > 1 else GROUP_NAME

    current_lamport = increment_lamport()
    msg_id = str(uuid.uuid4())
    sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    new_msg = FederatedMessage(
        **{
            "id": msg_id,
            "from": payload.from_user,
            "origin": origin,
            "lamport": current_lamport,
            "sent_at": sent_at,
            "body": payload.body,
        }
    )

    saved = save_incoming_message(new_msg, synced=0)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar el mensaje localmente.",
        )

    return {
        "status": "success",
        "message": "Mensaje creado y guardado localmente.",
        "data": new_msg.model_dump(by_alias=True),
    }


@router.get("/history")
def get_chat_history(since: Optional[int] = None):
    """Retorna el historial de mensajes ordenado por (lamport, origin)."""
    history = get_history(since_lamport=since)
    return {"history": history}