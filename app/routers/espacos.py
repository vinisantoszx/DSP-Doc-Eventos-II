from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.database import get_session
from app.models import (
    Espaco,
    EspacoCreate,
    EspacoPublicDetalhado,
    InfraestruturaEspaco,
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