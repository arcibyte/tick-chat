"""
Cliente de consola de tick-chat.

Habla SOLO con el servidor de nuestro grupo (nunca con el servidor central).
Usa únicamente la librería estándar de Python, así que no hay que instalar nada.

Uso:
    python client.py                          # servidor en http://localhost:8000
    python client.py http://192.168.1.20:8000 # otro servidor

    # o dentro del contenedor:
    docker compose exec server python client.py

Colores:
    verde    -> usuarios de nuestro grupo
    cian     -> usuarios de otros grupos
    amarillo -> mis propios mensajes
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SERVER_URL = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SERVER_URL", "http://localhost:8000")
SERVER_URL = SERVER_URL.rstrip("/")
POLL_INTERVAL = 2  # segundos entre cada consulta de mensajes nuevos

# Códigos ANSI para colores en la terminal
RESET = "\033[0m"
GRIS = "\033[90m"
VERDE = "\033[92m"
CIAN = "\033[96m"
AMARILLO = "\033[93m"
ROJO = "\033[91m"
NEGRITA = "\033[1m"

# En Windows, esta llamada activa el soporte de colores ANSI en la consola.
if os.name == "nt":
    os.system("")


# ---------------------------------------------------------------------------
# Funciones para hablar con el servidor (HTTP + JSON)
# ---------------------------------------------------------------------------
def peticion(metodo, ruta, datos=None):
    """Hace una petición HTTP al servidor y devuelve (codigo, respuesta_json)."""
    url = SERVER_URL + ruta
    cuerpo = None
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")

    req = urllib.request.Request(url, data=cuerpo, method=metodo)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            texto = resp.read().decode("utf-8")
            return resp.status, (json.loads(texto) if texto else {})
    except urllib.error.HTTPError as err:
        # El servidor respondió con un error (4xx o 5xx)
        texto = err.read().decode("utf-8")
        try:
            return err.code, json.loads(texto)
        except ValueError:
            return err.code, {"detail": texto}


def obtener_nombre_grupo():
    """Pregunta al servidor su nombre de grupo (g1, g2, ...) usando /fed/health."""
    _, datos = peticion("GET", "/fed/health")
    return datos.get("server", "?")


def crear_usuario(usuario):
    """Registra el usuario local. Si ya existe, no es un error: simplemente lo usamos."""
    codigo, datos = peticion("POST", "/users", {"username": usuario})
    if codigo in (200, 201):
        return True
    # Si ya está creado, lo confirmamos buscando en la lista de usuarios
    _, lista = peticion("GET", "/users")
    if usuario in lista.get("users", []):
        return True
    print(ROJO + "No se pudo crear el usuario: " + str(datos.get("detail")) + RESET)
    return False


def enviar_mensaje(usuario, texto):
    codigo, datos = peticion("POST", "/messages", {"from_user": usuario, "body": texto})
    if codigo not in (200, 201):
        print(ROJO + "Error al enviar (" + str(codigo) + "): " + str(datos.get("detail")) + RESET)


def obtener_historial():
    """Devuelve la lista de mensajes ordenada por (lamport, origin)."""
    _, datos = peticion("GET", "/history")
    if isinstance(datos, list):
        return datos
    return datos.get("history", [])


# ---------------------------------------------------------------------------
# Mostrar mensajes
# ---------------------------------------------------------------------------
def formatear(mensaje, mi_usuario, mi_grupo):
    """Devuelve una línea de texto con el color según quién escribió."""
    # El remitente puede venir como "from_user" o "from" según el servidor
    remitente = mensaje.get("from_user") or mensaje.get("from") or "?"
    origen = mensaje.get("origin", "?")
    lamport = mensaje.get("lamport", 0)
    cuerpo = mensaje.get("body", "")

    if remitente == mi_usuario:
        color = AMARILLO
    elif origen == mi_grupo:
        color = VERDE
    else:
        color = CIAN

    marca = GRIS + "[L" + str(lamport) + "]" + RESET
    return marca + " " + color + NEGRITA + remitente + RESET + ": " + cuerpo


def mostrar_historial_completo(mi_usuario, mi_grupo, vistos):
    print(GRIS + "----- #general (ordenado por lamport, origen) -----" + RESET)
    for mensaje in obtener_historial():
        print(formatear(mensaje, mi_usuario, mi_grupo))
        vistos.add(mensaje.get("id"))
    print(GRIS + "---------------------------------------------------" + RESET)


def escuchar_mensajes_nuevos(mi_usuario, mi_grupo, vistos, detener):
    """
    Hilo en segundo plano: cada POLL_INTERVAL segundos pide el historial
    e imprime los mensajes cuyo id todavía no hemos mostrado.
    Usamos el id (no el lamport) porque un mensaje que llega tarde puede
    tener una marca de Lamport menor que otros ya mostrados.
    """
    servidor_caido = False
    while not detener.is_set():
        try:
            for mensaje in obtener_historial():
                if mensaje.get("id") not in vistos:
                    vistos.add(mensaje.get("id"))
                    print("\r" + formatear(mensaje, mi_usuario, mi_grupo))
            if servidor_caido:
                print(GRIS + "(conexión con el servidor recuperada)" + RESET)
                servidor_caido = False
        except (urllib.error.URLError, OSError):
            if not servidor_caido:
                print(ROJO + "(no hay conexión con el servidor, reintentando...)" + RESET)
                servidor_caido = True
        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def mostrar_ayuda():
    print(GRIS + "Escriba un mensaje y presione Enter para enviarlo a #general." + RESET)
    print(GRIS + "Comandos:  /historial  muestra todo el historial ordenado" + RESET)
    print(GRIS + "           /usuarios   lista los usuarios de este servidor" + RESET)
    print(GRIS + "           /ayuda      muestra esta ayuda" + RESET)
    print(GRIS + "           /salir      cierra el cliente" + RESET)


def main():
    print(NEGRITA + "tick-chat" + RESET + " · conectando a " + SERVER_URL)
    try:
        grupo = obtener_nombre_grupo()
    except (urllib.error.URLError, OSError):
        print(ROJO + "No se pudo conectar con " + SERVER_URL + ". ¿Está corriendo el servidor?" + RESET)
        return

    nombre = ""
    while nombre == "" or "@" in nombre or " " in nombre:
        nombre = input("Nombre de usuario (sin @" + grupo + "): ").strip()
    usuario = nombre + "@" + grupo

    if not crear_usuario(usuario):
        return

    print("Conectado como " + AMARILLO + NEGRITA + usuario + RESET + " al servidor " + VERDE + grupo + RESET)
    print("Leyenda: " + VERDE + "mi grupo" + RESET + " · " + CIAN + "otros grupos" + RESET + " · " + AMARILLO + "yo" + RESET)
    mostrar_ayuda()

    vistos = set()
    mostrar_historial_completo(usuario, grupo, vistos)

    detener = threading.Event()
    hilo = threading.Thread(
        target=escuchar_mensajes_nuevos,
        args=(usuario, grupo, vistos, detener),
        daemon=True,
    )
    hilo.start()

    try:
        while True:
            texto = input().strip()
            if texto == "":
                continue
            if texto == "/salir":
                break
            elif texto == "/historial":
                mostrar_historial_completo(usuario, grupo, vistos)
            elif texto == "/usuarios":
                _, datos = peticion("GET", "/users")
                print(GRIS + "Usuarios de " + grupo + ": " + ", ".join(datos.get("users", [])) + RESET)
            elif texto == "/ayuda":
                mostrar_ayuda()
            else:
                try:
                    enviar_mensaje(usuario, texto)
                except (urllib.error.URLError, OSError):
                    print(ROJO + "No se pudo enviar: el servidor no responde." + RESET)
    except (KeyboardInterrupt, EOFError):
        pass

    detener.set()
    print("Hasta luego, " + usuario)


if __name__ == "__main__":
    main()
