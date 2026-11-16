import sqlite3
from typing import List, Optional
from app.config import DB_PATH
from app.schemas import FederatedMessage

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con tablas para usuarios, mensajes y el reloj de Lamport."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de usuarios locales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY
        )
    """)
    
    # Tabla de mensajes (sala global #general)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            from_user TEXT NOT NULL,
            origin TEXT NOT NULL,
            lamport INTEGER NOT NULL,
            sent_at TEXT NOT NULL,
            body TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    """)
    
    # Tabla para almacenar el estado actual del reloj de Lamport
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lamport_clock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            clock_value INTEGER NOT NULL
        )
    """)
    
    # Inicializar el reloj en 0 si no existe
    cursor.execute("""
        INSERT OR IGNORE INTO lamport_clock (id, clock_value) VALUES (1, 0)
    """)
    
    conn.commit()
    conn.close()

def get_lamport() -> int:
    """Retorna el valor actual del reloj de Lamport."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clock_value FROM lamport_clock WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row["clock_value"] if row else 0

def increment_lamport() -> int:
    """Incrementa el reloj de Lamport local antes de enviar un mensaje y lo retorna."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lamport_clock SET clock_value = clock_value + 1 WHERE id = 1")
    conn.commit()
    
    cursor.execute("SELECT clock_value FROM lamport_clock WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row["clock_value"]

def update_lamport_on_receive(received_lamport: int) -> int:
    """Actualiza el reloj al recibir un mensaje: max(local, recibido) + 1."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clock_value FROM lamport_clock WHERE id = 1")
    row = cursor.fetchone()
    local_clock = row["clock_value"] if row else 0
    
    new_clock = max(local_clock, received_lamport) + 1
    cursor.execute("UPDATE lamport_clock SET clock_value = ? WHERE id = 1", (new_clock,))
    conn.commit()
    conn.close()
    return new_clock

def save_incoming_message(msg: FederatedMessage, synced: int = 1) -> bool:
    """
    Guarda un mensaje aplicando deduplicación por ID.
    Retorna True si se guardó con éxito, False si ya existía (duplicado).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Usamos msg.from_ para acceder al campo correcto del esquema federado
        cursor.execute("""
            INSERT INTO messages (id, from_user, origin, lamport, sent_at, body, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg.id, msg.from_, msg.origin, msg.lamport, msg.sent_at, msg.body, synced))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def get_history(since_lamport: Optional[int] = None) -> List[dict]:
    """Retorna el historial ordenado por (lamport, origin) adaptando la clave 'from'."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if since_lamport is not None:
        cursor.execute("""
            SELECT id, from_user, origin, lamport, sent_at, body, synced 
            FROM messages 
            WHERE lamport > ? 
            ORDER BY lamport ASC, origin ASC
        """, (since_lamport,))
    else:
        cursor.execute("""
            SELECT id, from_user, origin, lamport, sent_at, body, synced 
            FROM messages 
            ORDER BY lamport ASC, origin ASC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Mapeamos 'from_user' a 'from' para que el cliente JSON lo lea correctamente
    history = []
    for row in rows:
        d = dict(row)
        d["from"] = d.pop("from_user")
        history.append(d)
    return history

def create_local_user(username: str) -> bool:
    """Registra un usuario local en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def get_local_users() -> List[str]:
    """Lista todos los usuarios locales."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row["username"] for row in rows]

def get_max_synced_lamport() -> int:
    """Retorna el lamport máximo de los mensajes sincronizados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(lamport), 0) FROM messages WHERE synced = 1")
    row = cursor.fetchone()
    conn.close()
    return int(row[0]) if row else 0

def mark_message_synced(msg_id: str, status: int = 1):
    """Actualiza el estado de sincronización de un mensaje en la BD."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET synced = ? WHERE id = ?", (status, msg_id))
    conn.commit()
    conn.close()

def get_pending_messages() -> List[FederatedMessage]:
    """Retorna los mensajes locales pendientes de sincronizar (synced = 0)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, from_user, origin, lamport, sent_at, body
        FROM messages
        WHERE synced = 0
        ORDER BY lamport ASC, origin ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        FederatedMessage(
            **{
                "id": row["id"],
                "from": row["from_user"],
                "origin": row["origin"],
                "lamport": row["lamport"],
                "sent_at": row["sent_at"],
                "body": row["body"],
            }
        )
        for row in rows
    ]