import logging
import time
from fastapi import FastAPI, Request
from app.database import create_db_and_tables
from app.routers import (
    bloqueios,
    espacos,
    recursos,
    relatorios,
    reservas,
    unidades,
    usuarios,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Reservas de Espaços",
    version="1.0.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.time()
    response = await call_next(request)
    duracao = round((time.time() - inicio) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} ({duracao}ms)"
    )
    return response


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/", tags=["Status"])
def health_check():
    return {"status": "online", "sistema": "Reservas de Espaços"}


app.include_router(unidades.router)
app.include_router(espacos.router)
app.include_router(usuarios.router)
app.include_router(recursos.router)
app.include_router(reservas.router)
app.include_router(bloqueios.router)
app.include_router(relatorios.router)