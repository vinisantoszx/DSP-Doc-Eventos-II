
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    BloqueioCreate,
    BloqueioEspaco,
    BloqueioPublic,
    Espaco,
    Reserva,
    StatusReserva,
)

router = APIRouter(
    prefix="/bloqueios",
    tags=["Bloqueios"],
)


def validar_intervalo(data_inicio: datetime, data_fim: datetime) -> None:
    if data_fim <= data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data de fim deve ser posterior à data de início.",
        )


def validar_espaco(espaco_id: int, session: Session) -> None:
    espaco = session.get(Espaco, espaco_id)

    if not espaco:
        raise HTTPException(
            status_code=404,
            detail="Espaço não encontrado.",
        )


def verificar_conflito_reserva(
    espaco_id: int,
    data_inicio: datetime,
    data_fim: datetime,
    session: Session,
) -> None:
    conflito = session.exec(
        select(Reserva).where(
            Reserva.espaco_id == espaco_id,
            Reserva.status.in_([
                StatusReserva.confirmada,
                StatusReserva.em_andamento,
            ]),
            Reserva.data_inicio < data_fim,
            Reserva.data_fim > data_inicio,
        )
    ).first()

    if conflito:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma reserva ativa nesse intervalo.",
        )


@router.post("/", response_model=BloqueioPublic, status_code=201)
def criar_bloqueio(
    dados: BloqueioCreate,
    session: Session = Depends(get_session),
):
    validar_intervalo(dados.data_inicio, dados.data_fim)
    validar_espaco(dados.espaco_id, session)

    verificar_conflito_reserva(
        dados.espaco_id,
        dados.data_inicio,
        dados.data_fim,
        session,
    )

    bloqueio = BloqueioEspaco.model_validate(dados)

    session.add(bloqueio)
    session.commit()
    session.refresh(bloqueio)

    return bloqueio
