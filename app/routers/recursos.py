from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.database import get_session
from app.models import (
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
