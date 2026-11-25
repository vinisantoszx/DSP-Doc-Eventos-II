from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    BloqueioEspaco,
    Espaco,
    Recurso,
    Reserva,
    ReservaCreate,
    ReservaPublicDetalhada,
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
    recursos: list[Recurso],
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

    # Impede uso simultâneo do mesmo recurso móvel em outro espaço no mesmo horário
    for recurso in recursos:
        consulta_conflito_recurso = (
            select(Reserva)
            .join(Reserva.recursos)
            .where(
                Recurso.id == recurso.id,
                Reserva.status.in_(status_ativos),
                Reserva.data_inicio < data_fim,
                Reserva.data_fim > data_inicio,
            )
        )

        if reserva_id_ignorar is not None:
            consulta_conflito_recurso = consulta_conflito_recurso.where(
                Reserva.id != reserva_id_ignorar
            )

        conflito_recurso = session.exec(
            consulta_conflito_recurso
        ).first()

        if conflito_recurso:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"O recurso '{recurso.nome}' já está reservado "
                    "em outro ambiente neste intervalo de horário."
                ),
            )


@router.post(
    "/",
    response_model=ReservaPublicDetalhada,
    status_code=201,
)
def criar_reserva(
    dados: ReservaCreate,
    session: Session = Depends(get_session),
):
    recursos = obter_recursos(
        dados.recurso_ids,
        session,
    )

    validar_regras_reserva(
        usuario_id=dados.usuario_id,
        espaco_id=dados.espaco_id,
        qtd_participantes=dados.qtd_participantes,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        recursos=recursos,
        session=session,
    )

    reserva = Reserva(
        **dados.model_dump(
            exclude={"recurso_ids"}
        ),
        recursos=recursos,
    )

    session.add(reserva)

    try:
        session.commit()
        session.refresh(reserva)
        return reserva
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível registrar a reserva por conflito de integridade.",
        )


@router.get(
    "/{reserva_id}",
    response_model=ReservaPublicDetalhada,
)
def buscar_reserva(
    reserva_id: int,
    session: Session = Depends(get_session),
):
    reserva = session.get(
        Reserva,
        reserva_id,
    )

    if not reserva:
        raise HTTPException(
            status_code=404,
            detail="Reserva não encontrada.",
        )

    return reserva
