from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.database import get_session
from app.models import (
    Espaco,
    EspacosMaisRequisitadosPublic,
    EstatisticasGeraisPublic,
    HistoricoUtilizacaoPublic,
    Recurso,
    Reserva,
    ReservaRecurso,
    ReservasPorUnidadePublic,
    StatusReserva,
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

@router.get(
    "/espacos-mais-requisitados",
    response_model=list[EspacosMaisRequisitadosPublic],
)
def espacos_mais_requisitados(
    session: Session = Depends(get_session),
):
    total_reservas = func.coalesce(
        func.count(Reserva.id), 0
    )

    consulta = (
        select(
            Espaco.id,
            Espaco.nome,
            total_reservas.label("total_reservas"),
        )
        .outerjoin(Reserva, Reserva.espaco_id == Espaco.id)
        .group_by(Espaco.id, Espaco.nome)
        .order_by(total_reservas.desc(), Espaco.nome)
    )

    resultados = session.exec(consulta).all()

    return [
        {
            "espaco_id": espaco_id,
            "espaco": nome,
            "total_reservas": quantidade,
        }
        for espaco_id, nome, quantidade in resultados
    ]

@router.get(
    "/reservas-por-unidade",
    response_model=list[ReservasPorUnidadePublic],
)
def reservas_por_unidade(
    session: Session = Depends(get_session),
):
    total_reservas = func.coalesce(
        func.count(Reserva.id), 0
    )

    consulta = (
        select(
            Unidade.id,
            Unidade.nome,
            total_reservas.label("total_reservas"),
        )
        .outerjoin(Espaco, Espaco.unidade_id == Unidade.id)
        .outerjoin(Reserva, Reserva.espaco_id == Espaco.id)
        .group_by(Unidade.id, Unidade.nome)
        .order_by(total_reservas.desc(), Unidade.nome)
    )

    resultados = session.exec(consulta).all()

    return [
        {
            "unidade_id": unidade_id,
            "unidade": nome,
            "total_reservas": quantidade,
        }
        for unidade_id, nome, quantidade in resultados
    ]

@router.get(
    "/estatisticas-gerais",
    response_model=EstatisticasGeraisPublic,
)
def estatisticas_gerais(
    session: Session = Depends(get_session),
):
    agora = datetime.now()

    reservas_futuras = session.exec(
        select(func.count(Reserva.id)).where(
            Reserva.status == StatusReserva.confirmada,
            Reserva.data_inicio > agora,
        )
    ).one()

    reservas_em_andamento = session.exec(
        select(func.count(Reserva.id)).where(
            Reserva.status == StatusReserva.em_andamento
        )
    ).one()

    reservas_canceladas = session.exec(
        select(func.count(Reserva.id)).where(
            Reserva.status == StatusReserva.cancelada
        )
    ).one()

    reservas_concluidas = session.exec(
        select(func.count(Reserva.id)).where(
            Reserva.status == StatusReserva.concluida
        )
    ).one()

    consulta_recursos = (
        select(
            Recurso.id,
            Recurso.nome,
            func.count(ReservaRecurso.reserva_id).label(
                "total_reservas"
            ),
        )
        .outerjoin(
            ReservaRecurso,
            ReservaRecurso.recurso_id == Recurso.id,
        )
        .group_by(Recurso.id, Recurso.nome)
        .order_by(
            func.count(ReservaRecurso.reserva_id).desc(),
            Recurso.nome,
        )
    )

    resultados_recursos = session.exec(consulta_recursos).all()

    recursos_mais_utilizados = [
        {
            "recurso_id": recurso_id,
            "recurso": nome,
            "total_reservas": quantidade,
        }
        for recurso_id, nome, quantidade in resultados_recursos
    ]

    return {
        "reservas_futuras": reservas_futuras,
        "reservas_em_andamento": reservas_em_andamento,
        "reservas_canceladas": reservas_canceladas,
        "reservas_concluidas": reservas_concluidas,
        "recursos_mais_utilizados": recursos_mais_utilizados,
    }