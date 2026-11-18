import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import GROUP_NAME
from app.database import init_db
from app.federation import background_supervisor
from app.routes_fed import router as fed_router
from app.routes_local import router as local_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    supervisor_task = asyncio.create_task(background_supervisor())
    yield
    supervisor_task.cancel()


app = FastAPI(title=f"TickChat Node - {GROUP_NAME}", lifespan=lifespan)

# Configuración de CORS para permitir peticiones desde el frontend web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite conexiones desde cualquier origen (ideal para desarrollo local)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fed_router)
app.include_router(local_router)