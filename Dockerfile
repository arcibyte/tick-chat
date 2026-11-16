# Imagen del servidor de grupo de tick-chat.
# Usamos una imagen oficial de Python, versión "slim" (más liviana).
FROM python:3.12-slim

# PYTHONUNBUFFERED=1 hace que los print/logs salgan de inmediato en
# "docker compose logs" (si no, Python los guarda en un buffer).
# PYTHONDONTWRITEBYTECODE=1 evita crear archivos .pyc dentro del contenedor.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Carpeta de trabajo dentro del contenedor.
WORKDIR /code

# Primero copiamos solo requirements.txt e instalamos las dependencias.
# Así Docker reutiliza esta capa en caché mientras requirements.txt no cambie,
# y reconstruir la imagen después de tocar el código es mucho más rápido.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora sí copiamos el código del servidor y el cliente.
COPY app ./app
COPY client.py .

# Carpeta donde vive la base de datos SQLite. En docker-compose.yml
# se monta un volumen aquí para que los datos sobrevivan a reinicios.
RUN mkdir -p /data

# Puerto en el que escucha uvicorn dentro del contenedor.
EXPOSE 8000

# Docker revisa cada 10 s que el servidor responda en /fed/health.
# Usamos Python (urllib) porque la imagen slim no trae curl.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/fed/health', timeout=2)" || exit 1

# Arranca el servidor FastAPI. --host 0.0.0.0 es obligatorio para que
# sea accesible desde fuera del contenedor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
