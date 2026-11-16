# Hallazgos al probar `main` (para Rol 1 y Rol 2)

Al montar el experimento, el servidor de `main` no cumple el flujo completo.
Cada punto fue verificado ejecutando el código.

1. **El servidor no arranca** (`ImportError`): `app/federation.py` importa
   `get_max_synced_lamport`, `get_pending_messages` y `mark_message_synced`,
   que no existen en `app/database.py`.
2. **`routes_local.py` falla al importarse**: la clase `UserCreate(BaseModel.model_config ...)`
   lanza `TypeError`. Se puede borrar (no se usa).
3. **`database.py` usa `msg.from_user`**, pero `FederatedMessage` define `from_`
   (alias `from`). Falla al guardar mensajes.
4. **`DB_PATH` está fijo en `"chat.db"`** en `database.py` e ignora la variable de
   entorno `DB_PATH`. En Docker la BD queda fuera del volumen `/data` y se pierde
   con `docker compose down` (incumple el requisito de persistencia).
5. **Los mensajes locales nunca se envían al central** si éste está en línea:
   `send_with_backoff` solo se invoca en `flush_pending_messages`, que corre
   únicamente al arrancar y al recuperarse el central. Falta un disparo al crear
   el mensaje o un flush en cada heartbeat exitoso.
6. (Observación) `send_with_backoff` se ejecuta dentro del supervisor: mientras
   reintenta, los heartbeats se detienen y el central no se marca caído.

El experimento se probó con una copia parcheada para 1–5 (no está en el repo).
