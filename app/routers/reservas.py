from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.models import (
    BloqueioEspaco,
    Espaco,
    Recurso,
    Reserva,
    StatusReserva,
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
    qtd_participantes: int,
    data_inicio: datetime,
    data_fim: datetime,
    session: Session,
    reserva_id_ignorar: int | None = None,
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

    # Valida intervalo de horário e capacidade do espaço
    if data_fim <= data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data de fim deve ser posterior à data de início.",
        )

    if qtd_participantes > espaco.capacidade:
        raise HTTPException(
            status_code=400,
            detail=(
                "A quantidade de participantes excede "
                "a capacidade máxima do espaço."
            ),
        )

    status_ativos = [
        StatusReserva.confirmada,
        StatusReserva.em_andamento,
    ]

    # Verifica conflito de horário com outras reservas ativas no mesmo espaço
    consulta_conflito_espaco = select(Reserva).where(
        Reserva.espaco_id == espaco_id,
        Reserva.status.in_(status_ativos),
        Reserva.data_inicio < data_fim,
        Reserva.data_fim > data_inicio,
    )

    if reserva_id_ignorar is not None:
        consulta_conflito_espaco = consulta_conflito_espaco.where(
            Reserva.id != reserva_id_ignorar
        )

    conflito_espaco = session.exec(
        consulta_conflito_espaco
    ).first()

    if conflito_espaco:
        raise HTTPException(
            status_code=409,
            detail="O espaço já possui uma reserva ativa neste intervalo de horário.",
        )

    # Verifica se há bloqueio de manutenção/limpeza no período
    conflito_bloqueio = session.exec(
        select(BloqueioEspaco).where(
            BloqueioEspaco.espaco_id == espaco_id,
            BloqueioEspaco.data_inicio < data_fim,
            BloqueioEspaco.data_fim > data_inicio,
        )
    ).first()

    if conflito_bloqueio:
        raise HTTPException(
            status_code=409,
            detail="O espaço possui um bloqueio ativo neste intervalo de horário.",
        )
