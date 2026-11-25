import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.database import get_session
from app.models import (
    Espaco,
    EspacoCreate,
    EspacoPublicDetalhado,
    EspacoUpdate,
    InfraestruturaEspaco,
    MetadadosPaginacao,
    PaginaEspacos,
    TipoEspaco,
    Unidade,
)

router = APIRouter(prefix="/espacos", tags=["Espacos"])


@router.post(
    "/",
    response_model=EspacoPublicDetalhado,
    status_code=status.HTTP_201_CREATED,
)
def criar_espaco(
    dados: EspacoCreate,
    session: Session = Depends(get_session),
):
    unidade = session.get(Unidade, dados.unidade_id)
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada",
        )
    if not unidade.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível cadastrar espaço em uma unidade inativa",
        )

    dados_espaco = dados.model_dump(exclude={"infraestrutura"})
    novo_espaco = Espaco(**dados_espaco)

    try:
        session.add(novo_espaco)
        session.flush()

        if dados.infraestrutura:
            nova_infra = InfraestruturaEspaco(
                **dados.infraestrutura.model_dump(),
                espaco_id=novo_espaco.id,
            )
            session.add(nova_infra)

        session.commit()
        session.refresh(novo_espaco)
        return novo_espaco
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro de integridade ao cadastrar o espaço",
        )


@router.get("/", response_model=PaginaEspacos)
def listar_espacos(
    nome: str | None = None,
    unidade_id: int | None = None,
    tipo: TipoEspaco | None = None,
    andar: int | None = None,
    capacidade_minima: int | None = Query(default=None, ge=1),
    ativo: bool | None = None,
    possui_projetor: bool | None = None,
    possui_som: bool | None = None,
    acessibilidade: bool | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho_pagina: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    consulta = select(Espaco).outerjoin(InfraestruturaEspaco)

    if nome:
        consulta = consulta.where(Espaco.nome.ilike(f"%{nome}%"))
    if unidade_id is not None:
        consulta = consulta.where(Espaco.unidade_id == unidade_id)
    if tipo is not None:
        consulta = consulta.where(Espaco.tipo == tipo)
    if andar is not None:
        consulta = consulta.where(Espaco.andar == andar)
    if capacidade_minima is not None:
        consulta = consulta.where(Espaco.capacidade >= capacidade_minima)
    if ativo is not None:
        consulta = consulta.where(Espaco.ativo == ativo)
    if possui_projetor is not None:
        consulta = consulta.where(
            InfraestruturaEspaco.possui_projetor == possui_projetor
        )
    if possui_som is not None:
        consulta = consulta.where(InfraestruturaEspaco.possui_som == possui_som)
    if acessibilidade is not None:
        consulta = consulta.where(
            InfraestruturaEspaco.acessibilidade == acessibilidade
        )

    total_itens = session.exec(
        select(func.count()).select_from(consulta.subquery())
    ).one()
    total_paginas = math.ceil(total_itens / tamanho_pagina) if total_itens > 0 else 0

    deslocamento = (pagina - 1) * tamanho_pagina
    espacos = session.exec(
        consulta.order_by(Espaco.id).offset(deslocamento).limit(tamanho_pagina)
    ).all()

    return PaginaEspacos(
        dados=espacos,
        paginacao=MetadadosPaginacao(
            total_itens=total_itens,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )


@router.get("/{espaco_id}", response_model=EspacoPublicDetalhado)
def buscar_espaco(
    espaco_id: int,
    session: Session = Depends(get_session),
):
    espaco = session.get(Espaco, espaco_id)
    if not espaco:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Espaço não encontrado",
        )
    return espaco


@router.patch("/{espaco_id}", response_model=EspacoPublicDetalhado)
def atualizar_espaco(
    espaco_id: int,
    dados: EspacoUpdate,
    session: Session = Depends(get_session),
):
    espaco = session.get(Espaco, espaco_id)
    if not espaco:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Espaço não encontrado",
        )

    if dados.unidade_id is not None:
        unidade = session.get(Unidade, dados.unidade_id)
        if not unidade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada",
            )
        if not unidade.ativa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível vincular espaço a uma unidade inativa",
            )

    dados_espaco = dados.model_dump(exclude_unset=True, exclude={"infraestrutura"})
    espaco.sqlmodel_update(dados_espaco)

    if dados.infraestrutura is not None:
        dados_infra = dados.infraestrutura.model_dump(exclude_unset=True)
        if espaco.infraestrutura:
            espaco.infraestrutura.sqlmodel_update(dados_infra)
            session.add(espaco.infraestrutura)
        else:
            nova_infra = InfraestruturaEspaco(**dados_infra, espaco_id=espaco.id)
            session.add(nova_infra)

    try:
        session.add(espaco)
        session.commit()
        session.refresh(espaco)
        return espaco
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro de integridade ao atualizar o espaço",
        )


@router.delete("/{espaco_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_espaco(
    espaco_id: int,
    session: Session = Depends(get_session),
):
    espaco = session.get(Espaco, espaco_id)
    if not espaco:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Espaço não encontrado",
        )

    if espaco.reservas or espaco.bloqueios:
        espaco.ativo = False
        session.add(espaco)
        session.commit()
        return

    if espaco.infraestrutura:
        session.delete(espaco.infraestrutura)

    session.delete(espaco)
    session.commit()