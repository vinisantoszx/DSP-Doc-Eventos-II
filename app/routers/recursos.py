from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    MetadadosPaginacao,
    PaginaRecursos,
    Recurso,
    RecursoCreate,
    RecursoPublic,
)

router = APIRouter(
    prefix="/recursos",
    tags=["Recursos"],
)


@router.post(
    "/",
    response_model=RecursoPublic,
    status_code=201,
)
def criar_recurso(
    dados: RecursoCreate,
    session: Session = Depends(get_session),
):
    recurso = Recurso.model_validate(dados)
    session.add(recurso)

    try:
        session.commit()
        session.refresh(recurso)
        return recurso
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Patrimônio já cadastrado.",
        )


@router.get(
    "/",
    response_model=PaginaRecursos,
)
def listar_recursos(
    pagina: int = Query(
        1,
        ge=1,
        description="Número da página.",
    ),
    tamanho_pagina: int = Query(
        10,
        ge=1,
        le=100,
        description="Quantidade de registros por página.",
    ),
    nome: str | None = Query(
        default=None,
        description="Filtra recursos pelo nome.",
    ),
    categoria: str | None = Query(
        default=None,
        description="Filtra recursos pela categoria/tipo.",
    ),
    disponivel: bool | None = Query(
        default=None,
        description="Filtra recursos pela disponibilidade.",
    ),
    session: Session = Depends(get_session),
):
    consulta = select(Recurso)
    consulta_total = (
        select(func.count())
        .select_from(Recurso)
    )

    if nome:
        filtro_nome = Recurso.nome.ilike(
            f"%{nome}%"
        )
        consulta = consulta.where(filtro_nome)
        consulta_total = consulta_total.where(filtro_nome)

    if categoria:
        filtro_categoria = Recurso.categoria.ilike(
            f"%{categoria}%"
        )
        consulta = consulta.where(filtro_categoria)
        consulta_total = consulta_total.where(filtro_categoria)

    if disponivel is not None:
        filtro_disponivel = (
            Recurso.disponivel == disponivel
        )
        consulta = consulta.where(filtro_disponivel)
        consulta_total = consulta_total.where(filtro_disponivel)

    total_itens = session.exec(
        consulta_total
    ).one()

    total_paginas = (
        total_itens + tamanho_pagina - 1
    ) // tamanho_pagina

    deslocamento = (
        pagina - 1
    ) * tamanho_pagina

    consulta = (
        consulta
        .order_by(Recurso.nome)
        .offset(deslocamento)
        .limit(tamanho_pagina)
    )

    recursos = session.exec(
        consulta
    ).all()

    return PaginaRecursos(
        dados=recursos,
        paginacao=MetadadosPaginacao(
            total_itens=total_itens,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )
