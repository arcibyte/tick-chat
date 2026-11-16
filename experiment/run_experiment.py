#!/usr/bin/env python3
"""Experimento: recuperación del servidor de grupo ante la caída del central.

Pregunta: ¿cuánto tarda en entregarse un lote de mensajes escritos mientras el
servidor central está caído, una vez que éste se recupera, según cuánto duró la
caída?  ¿Se pierde o se duplica algún mensaje?

Procedimiento de cada corrida (todo nuevo: central, servidor y base de datos):
    1. Levanta mock_central.py y un servidor de grupo (uvicorn, sin Docker).
    2. Espera a que el servidor se registre y crea un usuario local.
    3. Si duracion > 0: pone el central en estado "caído" (503 a todo).
    4. Envía N mensajes por la API local del servidor.
    5. Espera `duracion` segundos desde la caída y recupera el central.
    6. Mide el tiempo hasta que los N mensajes están en el central.

Variable independiente : duración de la caída (s).  0 = control sin caída.
Variable dependiente   : tiempo de recuperación (s) = última llegada al
                         central - instante en que el central se recuperó.
Controles              : N mensajes, intervalo de heartbeat y umbral de fallos
                         iguales en todas las corridas; 3 repeticiones.

Uso (desde la raíz del repositorio):
    python experiment/run_experiment.py
    python experiment/run_experiment.py --durations 0 2 5 10 20 40 --reps 3
    python experiment/run_experiment.py --app-dir /ruta/a/otra/copia

Solo usa la librería estándar; el servidor y el central necesitan las
dependencias de requirements.txt (pip install -r requirements.txt).
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUP = "gexp"


def http(method, url, body=None, timeout=5.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={"content-type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


def wait_until(predicate, timeout, step=0.1):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if predicate():
                return True
        except (urllib.error.URLError, ConnectionError, OSError, ValueError):
            pass
        time.sleep(step)
    return False


def run_once(args, duration, rep, workdir):
    central_url = f"http://127.0.0.1:{args.central_port}"
    server_url = f"http://127.0.0.1:{args.server_port}"
    log_path = Path(workdir) / f"server_d{duration}_r{rep}.log"
    procs = []
    try:
        env_c = {**os.environ, "PORT": str(args.central_port)}
        procs.append(subprocess.Popen(
            [sys.executable, str(ROOT / "mock_central.py")],
            env=env_c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ))
        if not wait_until(lambda: http("GET", f"{central_url}/health"), 15):
            raise RuntimeError("el central simulado no arrancó")

        db_dir = Path(workdir) / f"db_d{duration}_r{rep}"
        db_dir.mkdir(parents=True, exist_ok=True)
        env_s = {
            **os.environ,
            "GROUP_NAME": GROUP,
            "PUBLIC_URL": server_url,
            "CENTRAL_URL": central_url,
            "DB_PATH": str(db_dir / "tickchat.db"),
            "HEARTBEAT_INTERVAL": str(args.heartbeat),
            "MAX_HEALTH_FAILURES": str(args.max_failures),
            "REGISTER_INTERVAL": "30.0",
            "PYTHONPATH": str(args.app_dir),
            "PYTHONUNBUFFERED": "1",
        }
        with open(log_path, "w") as logf:
            procs.append(subprocess.Popen(
                [sys.executable, "-W", "ignore", "-m", "uvicorn", "app.main:app",
                 "--port", str(args.server_port), "--log-level", "warning"],
                cwd=db_dir, env=env_s, stdout=logf, stderr=subprocess.STDOUT,
            ))
        if not wait_until(lambda: http("GET", f"{server_url}/fed/health"), 20):
            raise RuntimeError("el servidor de grupo no arrancó (¿falló el import?)")
        if not wait_until(lambda: GROUP in http("GET", f"{central_url}/_admin/stats")["servers"], 15):
            raise RuntimeError("el servidor no se registró en el central")

        user = f"ana@{GROUP}"
        http("POST", f"{server_url}/users", {"username": user})

        t_down = None
        if duration > 0:
            t_down = http("POST", f"{central_url}/_admin/down")["t"]
            time.sleep(0.3)

        ids = []
        for i in range(args.messages):
            r = http("POST", f"{server_url}/messages", {"from_user": user, "body": f"msg {i}"})
            ids.append(r["data"]["id"])

        if duration > 0:
            time.sleep(max(0.0, t_down + duration - time.time()))
            t_up = http("POST", f"{central_url}/_admin/up")["t"]
        else:
            t_up = time.time()

        ok = wait_until(
            lambda: http("GET", f"{central_url}/_admin/stats")["unique_messages"] >= args.messages,
            args.timeout, step=0.05,
        )
        stats = http("GET", f"{central_url}/_admin/stats")
        delivered = sum(1 for i in ids if i in stats["arrivals"])
        recovery = (max(stats["arrivals"][i] for i in ids if i in stats["arrivals"]) - t_up
                    if ok else float("nan"))

        time.sleep(1.0)  # margen para detectar duplicados tardíos
        stats = http("GET", f"{central_url}/_admin/stats")
        log_text = log_path.read_text() if log_path.exists() else ""
        return {
            "outage_s": duration,
            "rep": rep,
            "n_messages": args.messages,
            "recovery_s": round(recovery, 3),
            "delivered": delivered,
            "lost": args.messages - delivered,
            "duplicates": stats["duplicate_posts"],
            "rejected_while_down": stats["rejected_while_down"],
            "retry_log_lines": log_text.count("SEND_RETRY"),
            "marked_down": int("CENTRAL_MARKED_DOWN" in log_text),
        }
    finally:
        for p in reversed(procs):
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--durations", type=float, nargs="+", default=[0, 2, 5, 10, 20, 40],
                    help="duración de la caída del central en segundos (0 = control)")
    ap.add_argument("--reps", type=int, default=3, help="repeticiones por duración")
    ap.add_argument("--messages", type=int, default=20, help="mensajes enviados durante la caída")
    ap.add_argument("--heartbeat", type=float, default=1.0, help="HEARTBEAT_INTERVAL (s)")
    ap.add_argument("--max-failures", type=int, default=3, help="MAX_HEALTH_FAILURES")
    ap.add_argument("--timeout", type=float, default=120.0, help="espera máxima por corrida (s)")
    ap.add_argument("--central-port", type=int, default=9100)
    ap.add_argument("--server-port", type=int, default=8101)
    ap.add_argument("--app-dir", type=Path, default=ROOT,
                    help="carpeta que contiene el paquete app/ a medir (por defecto, este repo)")
    ap.add_argument("--out", type=Path, default=ROOT / "experiment" / "results.csv")
    args = ap.parse_args()
    args.app_dir = args.app_dir.resolve()

    rows = []
    with tempfile.TemporaryDirectory(prefix="tickchat-exp-") as workdir:
        for duration in args.durations:
            for rep in range(1, args.reps + 1):
                print(f"[caída={duration:g}s  rep={rep}/{args.reps}] ...", end=" ", flush=True)
                row = run_once(args, duration, rep, workdir)
                rows.append(row)
                print(f"recuperación={row['recovery_s']} s  entregados={row['delivered']}/{args.messages}"
                      f"  duplicados={row['duplicates']}  reintentos(503)={row['rejected_while_down']}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nResultados guardados en {args.out}")


if __name__ == "__main__":
    main()
