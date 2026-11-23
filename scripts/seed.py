from sqlmodel import Session, select

from app.database import engine
from app.models import Unidade


def popular_unidades(session: Session) -> None:
    unidades = [
        Unidade(
            nome="Unidade Acadêmica de Tecnologia",
            endereco="Campus universitário",
            predio="Bloco A",
        ),
        Unidade(
            nome="Unidade Acadêmica de Ciências",
            endereco="Campus universitário",
            predio="Bloco B",
        ),
        Unidade(
            nome="Unidade Administrativa",
            endereco="Campus universitário",
            predio="Bloco Administrativo",
            ativa=False,
        ),
    ]

    unidades_cadastradas = session.exec(
        select(Unidade)
    ).all()

    nomes_existentes = {
        unidade.nome for unidade in unidades_cadastradas
    }

    for unidade in unidades:
        if unidade.nome not in nomes_existentes:
            session.add(unidade)

    session.commit()


def main() -> None:
    with Session(engine) as session:
        popular_unidades(session)


if __name__ == "__main__":
    main()
