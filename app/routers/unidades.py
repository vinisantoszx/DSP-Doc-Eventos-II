import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.models import (
    Espaco,
    EspacoPublicDetalhado,
    MetadadosPaginacao,
    PaginaUnidades,
    Unidade,
    UnidadeCreate,
    UnidadePublic,
    UnidadeUpdate,
)

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.post("/", response_model=UnidadePublic, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    dados: UnidadeCreate,
    session: Session = Depends(get_session),
):
    nova_unidade = Unidade.model_validate(dados)
    try:
        session.add(nova_unidade)
        session.commit()
        session.refresh(nova_unidade)
        return nova_unidade
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro de integridade ao cadastrar a unidade",
        )


@router.get("/", response_model=PaginaUnidades)
def listar_unidades(
    nome: str | None = None,
    predio: str | None = None,
    ativa: bool | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho_pagina: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    consulta = select(Unidade)

    if nome:
        consulta = consulta.where(col(Unidade.nome).ilike(f"%{nome}%"))
    if predio:
        consulta = consulta.where(col(Unidade.predio).ilike(f"%{predio}%"))
    if ativa is not None:
        consulta = consulta.where(Unidade.ativa == ativa)

    total_itens = session.exec(
        select(func.count()).select_from(consulta.subquery())
    ).one()
    total_paginas = math.ceil(total_itens / tamanho_pagina) if total_itens > 0 else 0

    deslocamento = (pagina - 1) * tamanho_pagina
    unidades = session.exec(
        consulta.order_by(Unidade.id).offset(deslocamento).limit(tamanho_pagina)
    ).all()

    return PaginaUnidades(
        dados=unidades,
        paginacao=MetadadosPaginacao(
            total_itens=total_itens,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )


@router.get("/{unidade_id}", response_model=UnidadePublic)
def buscar_unidade(
    unidade_id: int,
    session: Session = Depends(get_session),
):
    unidade = session.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada",
        )
    return unidade


@router.get("/{unidade_id}/espacos", response_model=list[EspacoPublicDetalhado])
def listar_espacos_da_unidade(
    unidade_id: int,
    ativo: bool | None = None,
    session: Session = Depends(get_session),
):
    unidade = session.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada",
        )

    consulta = select(Espaco).where(Espaco.unidade_id == unidade_id)
    if ativo is not None:
        consulta = consulta.where(Espaco.ativo == ativo)

    return session.exec(consulta.order_by(Espaco.id)).all()


@router.patch("/{unidade_id}", response_model=UnidadePublic)
def atualizar_unidade(
    unidade_id: int,
    dados: UnidadeUpdate,
    session: Session = Depends(get_session),
):
    unidade = session.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada",
        )

    dados_atualizados = dados.model_dump(exclude_unset=True)
    unidade.sqlmodel_update(dados_atualizados)

    try:
        session.add(unidade)
        session.commit()
        session.refresh(unidade)
        return unidade
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro de integridade ao atualizar a unidade",
        )


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_unidade(
    unidade_id: int,
    session: Session = Depends(get_session),
):
    unidade = session.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada",
        )

    if unidade.espacos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível remover uma unidade que possui espaços vinculados",
        )

    session.delete(unidade)
    session.commit()