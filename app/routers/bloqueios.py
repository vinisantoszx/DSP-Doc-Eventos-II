
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    BloqueioCreate,
    BloqueioEspaco,
    BloqueioPublic,
    BloqueioPublicDetalhado,
    BloqueioUpdate,
    Espaco,
    MetadadosPaginacao,
    PaginaBloqueios,
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


@router.get("/", response_model=PaginaBloqueios)
def listar_bloqueios(
    pagina: int = Query(default=1, ge=1),
    tamanho_pagina: int = Query(default=10, ge=1, le=100),
    espaco_id: int | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    session: Session = Depends(get_session),
):
    if inicio and fim and fim <= inicio:
        raise HTTPException(
            status_code=400,
            detail="O fim do período deve ser posterior ao início.",
        )

    consulta = select(BloqueioEspaco)
    consulta_total = select(
        func.count()
    ).select_from(BloqueioEspaco)

    if espaco_id is not None:
        consulta = consulta.where(
            BloqueioEspaco.espaco_id == espaco_id
        )
        consulta_total = consulta_total.where(
            BloqueioEspaco.espaco_id == espaco_id
        )

    if inicio:
        consulta = consulta.where(
            BloqueioEspaco.data_fim >= inicio
        )
        consulta_total = consulta_total.where(
            BloqueioEspaco.data_fim >= inicio
        )

    if fim:
        consulta = consulta.where(
            BloqueioEspaco.data_inicio <= fim
        )
        consulta_total = consulta_total.where(
            BloqueioEspaco.data_inicio <= fim
        )

    total_registros = session.exec(consulta_total).one()
    total_paginas = (
        (total_registros + tamanho_pagina - 1) // tamanho_pagina
    )

    consulta = consulta.order_by(
        BloqueioEspaco.data_inicio
    )

    consulta = consulta.offset(
        (pagina - 1) * tamanho_pagina
    ).limit(tamanho_pagina)

    bloqueios = session.exec(consulta).all()

    return PaginaBloqueios(
        dados=bloqueios,
        paginacao=MetadadosPaginacao(
            total_itens=total_registros,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )


@router.get("/{bloqueio_id}", response_model=BloqueioPublicDetalhado)
def buscar_bloqueio(
    bloqueio_id: int,
    session: Session = Depends(get_session),
):
    bloqueio = session.get(BloqueioEspaco, bloqueio_id)

    if not bloqueio:
        raise HTTPException(
            status_code=404,
            detail="Bloqueio não encontrado.",
        )

    return bloqueio


@router.patch("/{bloqueio_id}", response_model=BloqueioPublic)
def atualizar_bloqueio(
    bloqueio_id: int,
    dados: BloqueioUpdate,
    session: Session = Depends(get_session),
):
    bloqueio = session.get(BloqueioEspaco, bloqueio_id)

    if not bloqueio:
        raise HTTPException(
            status_code=404,
            detail="Bloqueio não encontrado.",
        )

    dados_atualizacao = dados.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not dados_atualizacao:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar.",
        )

    espaco_id = dados_atualizacao.get(
        "espaco_id", bloqueio.espaco_id
    )
    data_inicio = dados_atualizacao.get(
        "data_inicio", bloqueio.data_inicio
    )
    data_fim = dados_atualizacao.get(
        "data_fim", bloqueio.data_fim
    )

    validar_intervalo(data_inicio, data_fim)
    validar_espaco(espaco_id, session)

    verificar_conflito_reserva(
        espaco_id,
        data_inicio,
        data_fim,
        session,
    )

    bloqueio.sqlmodel_update(dados_atualizacao)

    session.add(bloqueio)
    session.commit()
    session.refresh(bloqueio)

    return bloqueio


@router.delete("/{bloqueio_id}", status_code=204)
def excluir_bloqueio(
    bloqueio_id: int,
    session: Session = Depends(get_session),
):
    bloqueio = session.get(BloqueioEspaco, bloqueio_id)

    if not bloqueio:
        raise HTTPException(
            status_code=404,
            detail="Bloqueio não encontrado.",
        )

    session.delete(bloqueio)
    session.commit()
