from typing import List
from app.schemas import FederatedMessage


def init_db():
    pass


def get_lamport() -> int:
    return 0


def increment_lamport() -> int:
    return 1


def update_lamport_on_receive(received_lamport: int) -> int:
    return received_lamport + 1


def save_incoming_message(msg: FederatedMessage) -> bool:
    return True


def mark_message_synced(msg_id: str, status: int = 1):
    pass


def get_max_synced_lamport() -> int:
    return 0


def get_pending_messages() -> List[FederatedMessage]:
    return []
