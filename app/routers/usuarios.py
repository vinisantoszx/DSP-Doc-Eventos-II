from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    MetadadosPaginacao,
    PaginaReservas,
    PaginaUsuarios,
    Reserva,
    Usuario,
    UsuarioCreate,
    UsuarioPublic,
    UsuarioUpdate,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
)


@router.post(
    "/",
    response_model=UsuarioPublic,
    status_code=201,
)
def criar_usuario(
    dados: UsuarioCreate,
    session: Session = Depends(get_session),
):
    usuario = Usuario.model_validate(dados)
    session.add(usuario)

    try:
        session.commit()
        session.refresh(usuario)
        return usuario
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="E-mail ou matrícula já cadastrados.",
        )


@router.get(
    "/",
    response_model=PaginaUsuarios,
)
def listar_usuarios(
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
        description="Filtra usuários pelo nome.",
    ),
    departamento: str | None = Query(
        default=None,
        description="Filtra usuários pelo departamento.",
    ),
    ativo: bool | None = Query(
        default=None,
        description="Filtra usuários pelo status de ativo ou inativo.",
    ),
    session: Session = Depends(get_session),
):
    consulta = select(Usuario)
    consulta_total = (
        select(func.count())
        .select_from(Usuario)
    )

    if nome:
        filtro_nome = Usuario.nome.ilike(
            f"%{nome}%"
        )
        consulta = consulta.where(filtro_nome)
        consulta_total = consulta_total.where(filtro_nome)

    if departamento:
        filtro_departamento = Usuario.departamento.ilike(
            f"%{departamento}%"
        )
        consulta = consulta.where(filtro_departamento)
        consulta_total = consulta_total.where(filtro_departamento)

    if ativo is not None:
        filtro_ativo = (
            Usuario.ativo == ativo
        )
        consulta = consulta.where(filtro_ativo)
        consulta_total = consulta_total.where(filtro_ativo)

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
        .order_by(Usuario.nome)
        .offset(deslocamento)
        .limit(tamanho_pagina)
    )

    usuarios = session.exec(
        consulta
    ).all()

    return PaginaUsuarios(
        dados=usuarios,
        paginacao=MetadadosPaginacao(
            total_itens=total_itens,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioPublic,
)
def buscar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
):
    usuario = session.get(
        Usuario,
        usuario_id,
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    return usuario


# Lista o histórico de reservas de um usuário específico
@router.get(
    "/{usuario_id}/reservas",
    response_model=PaginaReservas,
)
def listar_reservas_por_usuario(
    usuario_id: int,
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
    session: Session = Depends(get_session),
):
    usuario = session.get(
        Usuario,
        usuario_id,
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    filtro_usuario = (
        Reserva.usuario_id == usuario_id
    )

    consulta = (
        select(Reserva)
        .where(filtro_usuario)
    )
    consulta_total = (
        select(func.count())
        .select_from(Reserva)
        .where(filtro_usuario)
    )

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
        .order_by(Reserva.data_inicio.desc())
        .offset(deslocamento)
        .limit(tamanho_pagina)
    )

    reservas = session.exec(
        consulta
    ).all()

    return PaginaReservas(
        dados=reservas,
        paginacao=MetadadosPaginacao(
            total_itens=total_itens,
            total_paginas=total_paginas,
            pagina_atual=pagina,
            tamanho_pagina=tamanho_pagina,
        ),
    )


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioPublic,
)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    session: Session = Depends(get_session),
):
    usuario = session.get(
        Usuario,
        usuario_id,
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    dados_atualizacao = dados.model_dump(
        exclude_unset=True
    )

    usuario.sqlmodel_update(
        dados_atualizacao
    )

    session.add(usuario)

    try:
        session.commit()
        session.refresh(usuario)
        return usuario
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="E-mail ou matrícula já cadastrados.",
        )


@router.delete(
    "/{usuario_id}",
    status_code=204,
)
def excluir_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
):
    usuario = session.get(
        Usuario,
        usuario_id,
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    # Se já tiver reserva associada, apenas desativa para manter o histórico
    reserva_vinculada = session.exec(
        select(Reserva).where(
            Reserva.usuario_id == usuario_id
        )
    ).first()

    if reserva_vinculada:
        usuario.ativo = False
        session.add(usuario)
        session.commit()
        return

    session.delete(usuario)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Usuário possui reservas associadas "
                "e não pode ser removido."
            ),
        )
