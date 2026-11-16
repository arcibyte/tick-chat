from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import uuid
from datetime import datetime
from app.database import (
    init_db,
    create_local_user,
    get_local_users,
    save_incoming_message,
    get_history,
    increment_lamport,
    get_lamport
)
from app.schemas import FederatedMessage

router = APIRouter(tags=["Local API"])

class UserCreate(BaseModel.model_config if hasattr(BaseModel, 'model_config') else object):
    pass

# Como Pydantic puede variar ligeramente según la versión, definimos los modelos de entrada de forma sencilla:
from pydantic import BaseModel

class UserRequest(BaseModel):
    username: str

class MessageSendRequest(BaseModel):
    from_user: str
    body: str

@router.on_event("startup")
def startup_db():
    init_db()

@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRequest):
    """Crea un usuario local (ej: ana@g3)."""
    success = create_local_user(payload.username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe o el formato es inválido."
        )
    return {"message": f"Usuario {payload.username} creado con éxito."}

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
    # Validar que el usuario exista localmente
    users = get_local_users()
    if payload.from_user not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El remitente no es un usuario local registrado en este servidor."
        )
    
    # Extraer el origen (grupo) desde el usuario (ej: ana@g3 -> origin = g3)
    parts = payload.from_user.split("@")
    origin = parts[1] if len(parts) > 1 else "g_unknown"
    
    # Incrementar el reloj lógico de Lamport
    current_lamport = increment_lamport()
    
    # Crear el mensaje federado con UUID único
    msg_id = str(uuid.uuid4())
    sent_at = datetime.utcnow().isoformat() + "Z"
    
    new_msg = FederatedMessage(
        id=msg_id,
        from_user=payload.from_user,
        origin=origin,
        lamport=current_lamport,
        sent_at=sent_at,
        body=payload.body
    )
    
    # Guardar en la base de datos local
    saved = save_incoming_message(new_msg, synced=0) # synced=0 indica pendiente de enviar al central (Rol 3)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar el mensaje localmente."
        )
        
    return {
        "status": "success",
        "message": "Mensaje creado y guardado localmente.",
        "data": new_msg.dict() if hasattr(new_msg, 'dict') else new_msg.model_dump()
    }

@router.get("/history")
def get_chat_history(since: int = None):
    """Retorna el historial de mensajes ordenado por (lamport, origin)."""
    history = get_history(since_lamport=since)
    return {"history": history}