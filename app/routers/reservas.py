from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app.models import (
    Espaco,
    Recurso,
    Usuario,
)

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


def validar_regras_reserva(
    usuario_id: int,
    espaco_id: int,
    session: Session,
):
    usuario = session.get(
        Usuario,
        usuario_id,
    )
    espaco = session.get(
        Espaco,
        espaco_id,
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    if not espaco:
        raise HTTPException(
            status_code=404,
            detail="Espaço não encontrado.",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=400,
            detail="Usuário está inativo.",
        )

    if not espaco.ativo:
        raise HTTPException(
            status_code=400,
            detail="Espaço está inativo.",
        )
