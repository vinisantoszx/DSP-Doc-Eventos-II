from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    Espaco,
    HistoricoUtilizacaoPublic,
    Reserva,
    Unidade,
    Usuario,
)

router = APIRouter(prefix="/relatorios", tags=["Relatorios"])


@router.get(
    "/historico-utilizacao",
    response_model=list[HistoricoUtilizacaoPublic],
)
def historico_utilizacao(
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    unidade_id: int | None = None,
    session: Session = Depends(get_session),
):
    if data_inicio and data_fim and data_fim <= data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data final deve ser posterior à data inicial.",
        )

    consulta = (
        select(Reserva, Espaco, Unidade, Usuario)
        .join(Espaco, Reserva.espaco_id == Espaco.id)
        .join(Unidade, Espaco.unidade_id == Unidade.id)
        .join(Usuario, Reserva.usuario_id == Usuario.id)
    )

    if data_inicio:
        data_inicio = data_inicio.replace(tzinfo=None)
        consulta = consulta.where(
            Reserva.data_fim >= data_inicio
        )

    if data_fim:
        data_fim = data_fim.replace(tzinfo=None)
        consulta = consulta.where(
            Reserva.data_inicio <= data_fim
        )

    if unidade_id is not None:
        consulta = consulta.where(
            Unidade.id == unidade_id
        )

    consulta = consulta.order_by(Reserva.data_inicio)

    resultados = session.exec(consulta).all()

    return [
        {
            "reserva_id": reserva.id,
            "finalidade": reserva.finalidade,
            "qtd_participantes": reserva.qtd_participantes,
            "data_inicio": reserva.data_inicio,
            "data_fim": reserva.data_fim,
            "status": reserva.status,
            "espaco": espaco.nome,
            "unidade": unidade.nome,
            "usuario": usuario.nome,
        }
        for reserva, espaco, unidade, usuario in resultados
    ]