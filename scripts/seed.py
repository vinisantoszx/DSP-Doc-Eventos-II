from sqlmodel import Session, select

from app.database import engine
from app.models import Recurso, Unidade, Usuario

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

def popular_usuarios(session: Session) -> None:
    usuarios = [
        Usuario(
            nome="Ana Souza",
            email="ana.souza@example.com",
            matricula="2026001",
            departamento="Computação",
        ),
        Usuario(
            nome="Carlos Lima",
            email="carlos.lima@example.com",
            matricula="2026002",
            departamento="Matemática",
        ),
        Usuario(
            nome="Mariana Costa",
            email="mariana.costa@example.com",
            matricula="2026003",
            departamento="Engenharia",
        ),
        Usuario(
            nome="Pedro Alves",
            email="pedro.alves@example.com",
            matricula="2026004",
            departamento="Administração",
        ),
        Usuario(
            nome="Julia Martins",
            email="julia.martins@example.com",
            matricula="2026005",
            departamento="Computação",
            ativo=False,
        ),
    ]

    usuarios_cadastrados = session.exec(
        select(Usuario)
    ).all()

    emails_existentes = {
        usuario.email for usuario in usuarios_cadastrados
    }

    for usuario in usuarios:
        if usuario.email not in emails_existentes:
            session.add(usuario)

    session.commit()


def popular_recursos(session: Session) -> None:
    recursos = [
        Recurso(
            nome="Projetor Epson",
            patrimonio="REC-001",
            categoria="Projetor",
        ),
        Recurso(
            nome="Caixa de som JBL",
            patrimonio="REC-002",
            categoria="Áudio",
        ),
        Recurso(
            nome="Notebook Dell",
            patrimonio="REC-003",
            categoria="Computador",
        ),
        Recurso(
            nome="Microfone sem fio",
            patrimonio="REC-004",
            categoria="Áudio",
        ),
        Recurso(
            nome="Webcam Logitech",
            patrimonio="REC-005",
            categoria="Vídeo",
            disponivel=False,
        ),
    ]

    recursos_cadastrados = session.exec(
        select(Recurso)
    ).all()

    patrimonios_existentes = {
        recurso.patrimonio for recurso in recursos_cadastrados
    }

    for recurso in recursos:
        if recurso.patrimonio not in patrimonios_existentes:
            session.add(recurso)

    session.commit()

def main() -> None:
    with Session(engine) as session:
        popular_unidades(session)
        popular_usuarios(session)
        popular_recursos(session)


if __name__ == "__main__":
    main()
