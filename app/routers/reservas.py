from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app.models import Recurso

router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"],
)


def obter_recursos(
    ids: list[int],
    session: Session,
) -> list[Recurso]:
    recursos = []

    for recurso_id in set(ids):
        recurso = session.get(
            Recurso,
            recurso_id,
        )

        if not recurso:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Recurso {recurso_id} "
                    "não encontrado."
                ),
            )

        if not recurso.disponivel:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Recurso {recurso.nome} "
                    "está indisponível."
                ),
            )

        recursos.append(recurso)

    return recursos
