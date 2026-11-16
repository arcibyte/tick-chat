"""Servidor central simulado para pruebas locales de tick-chat.

Imita al servidor central del profesor con la API del protocolo:

    POST /register   {"server": "g3", "url": "http://..."}
    POST /messages   mensaje federado (id, from, origin, lamport, sent_at, body)
    GET  /history    ?since=<lamport>  -> mensajes con lamport > since
    GET  /health

Además expone endpoints de control (prefijo /_admin) para el experimento:

    POST /_admin/down    el central "se cae": todo responde 503
    POST /_admin/up      el central se recupera
    POST /_admin/reset   borra mensajes, registros y contadores
    GET  /_admin/stats   contadores y marcas de tiempo de cada mensaje

Uso:
    python mock_central.py              # puerto 9000
    PORT=9100 python mock_central.py

Dependencias: las mismas de requirements.txt (fastapi, uvicorn, httpx).
"""
import asyncio
import logging
import os
import time

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PORT = int(os.getenv("PORT", "9000"))
# Probabilidad (0..1) de responder 503 a un POST /messages, para probar reintentos.
FAIL_RATE = float(os.getenv("FAIL_RATE", "0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [mock-central] %(message)s",
)
log = logging.getLogger("mock-central")

app = FastAPI(title="Mock central tick-chat")

servers: dict[str, str] = {}          # nombre de grupo -> url pública
messages: dict[str, dict] = {}        # id -> mensaje (sin duplicados)
arrivals: dict[str, float] = {}       # id -> time.time() de la primera llegada
duplicate_posts = 0                   # POST /messages repetidos (mismo id)
rejected_while_down = 0               # peticiones respondidas con 503
is_down = False
_rng_state = 12345                    # LCG simple: reproducible, sin importar random


def _rand() -> float:
    global _rng_state
    _rng_state = (1103515245 * _rng_state + 12345) % (2**31)
    return _rng_state / 2**31


@app.middleware("http")
async def simulate_outage(request: Request, call_next):
    global rejected_while_down
    if is_down and not request.url.path.startswith("/_admin"):
        rejected_while_down += 1
        return JSONResponse({"detail": "central caido (simulado)"}, status_code=503)
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/register")
async def register(payload: dict):
    name, url = payload.get("server"), payload.get("url")
    if not name or not url:
        return JSONResponse({"detail": "faltan server/url"}, status_code=422)
    servers[name] = url
    log.info(f"REGISTER server={name} url={url}")
    return {"status": "ok"}


@app.post("/messages")
async def post_message(msg: dict):
    global duplicate_posts
    required = ("id", "from", "origin", "lamport", "sent_at", "body")
    missing = [k for k in required if k not in msg]
    if missing:
        return JSONResponse({"detail": f"faltan campos: {missing}"}, status_code=422)

    if FAIL_RATE and _rand() < FAIL_RATE:
        log.info(f"FAIL_INJECTED id={msg['id']}")
        return JSONResponse({"detail": "fallo inyectado"}, status_code=503)

    if msg["id"] in messages:
        duplicate_posts += 1
        log.info(f"DUPLICATE id={msg['id']}")
        return {"status": "ok", "duplicate": True}

    messages[msg["id"]] = msg
    arrivals[msg["id"]] = time.time()
    log.info(f"MESSAGE id={msg['id']} from={msg['from']} lamport={msg['lamport']}")
    asyncio.create_task(fan_out(msg))
    return {"status": "ok"}


async def fan_out(msg: dict):
    """Reenvía el mensaje a los demás servidores registrados (POST /fed/messages)."""
    targets = {n: u for n, u in servers.items() if n != msg["origin"]}
    async with httpx.AsyncClient() as client:
        for name, url in targets.items():
            try:
                r = await client.post(f"{url}/fed/messages", json=msg, timeout=3.0)
                log.info(f"FANOUT id={msg['id']} to={name} status={r.status_code}")
            except Exception as exc:
                log.warning(f"FANOUT_FAIL id={msg['id']} to={name} error={exc}")


@app.get("/history")
async def history(since: int = 0):
    out = [m for m in messages.values() if m["lamport"] > since]
    out.sort(key=lambda m: (m["lamport"], m["origin"]))
    return {"messages": out}


# ---------------- control para el experimento ----------------

@app.post("/_admin/down")
async def admin_down():
    global is_down
    is_down = True
    log.warning("ADMIN central CAIDO")
    return {"down": True, "t": time.time()}


@app.post("/_admin/up")
async def admin_up():
    global is_down
    is_down = False
    log.warning("ADMIN central RECUPERADO")
    return {"down": False, "t": time.time()}


@app.post("/_admin/reset")
async def admin_reset():
    global duplicate_posts, rejected_while_down, is_down
    messages.clear()
    arrivals.clear()
    servers.clear()
    duplicate_posts = rejected_while_down = 0
    is_down = False
    return {"status": "reset"}


@app.get("/_admin/stats")
async def admin_stats():
    return {
        "down": is_down,
        "servers": servers,
        "unique_messages": len(messages),
        "duplicate_posts": duplicate_posts,
        "rejected_while_down": rejected_while_down,
        "arrivals": arrivals,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
