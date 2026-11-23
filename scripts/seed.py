from sqlmodel import Session, select

from app.database import engine
from app.models import (
    Espaco,
    InfraestruturaEspaco,
    Recurso,
    TipoEspaco,
    Unidade,
    Usuario,
)

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


def popular_espacos(session: Session) -> None:
    unidades = {
        unidade.nome: unidade
        for unidade in session.exec(select(Unidade)).all()
    }

    unidade_tecnologia = unidades["Unidade Acadêmica de Tecnologia"]
    unidade_ciencias = unidades["Unidade Acadêmica de Ciências"]
    unidade_administrativa = unidades["Unidade Administrativa"]

    espacos = [
        Espaco(
            nome="Auditório Central",
            tipo=TipoEspaco.auditorio,
            capacidade=200,
            descricao="Auditório principal com palco e cabine de som",
            andar=0,
            unidade_id=unidade_tecnologia.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
                possui_som=True,
                acessibilidade=True,
            ),
        ),
        Espaco(
            nome="Laboratório de Informática 1",
            tipo=TipoEspaco.laboratorio,
            capacidade=40,
            descricao="Laboratório com computadores para aulas práticas",
            andar=1,
            unidade_id=unidade_tecnologia.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
                qtd_computadores=40,
                acessibilidade=True,
            ),
        ),
        Espaco(
            nome="Laboratório de Informática 2",
            tipo=TipoEspaco.laboratorio,
            capacidade=30,
            descricao="Laboratório com computadores para aulas práticas",
            andar=1,
            unidade_id=unidade_tecnologia.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
                qtd_computadores=30,
            ),
        ),
        Espaco(
            nome="Sala de Reuniões A1",
            tipo=TipoEspaco.sala_reuniao,
            capacidade=12,
            descricao="Sala para reuniões de grupos de pesquisa",
            andar=2,
            unidade_id=unidade_tecnologia.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
            ),
        ),
        Espaco(
            nome="Sala de Treinamento B1",
            tipo=TipoEspaco.sala_treinamento,
            capacidade=25,
            descricao="Sala para cursos e treinamentos",
            andar=1,
            unidade_id=unidade_ciencias.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
                possui_som=True,
            ),
        ),
        Espaco(
            nome="Laboratório de Química",
            tipo=TipoEspaco.laboratorio,
            capacidade=20,
            descricao="Laboratório para aulas práticas de química",
            andar=0,
            unidade_id=unidade_ciencias.id,
            infraestrutura=InfraestruturaEspaco(
                climatizado=False,
                observacoes="Uso somente com acompanhamento do técnico",
            ),
        ),
        Espaco(
            nome="Espaço Multiuso B2",
            tipo=TipoEspaco.multiuso,
            capacidade=80,
            descricao="Espaço para eventos e atividades diversas",
            unidade_id=unidade_ciencias.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
                possui_som=True,
                acessibilidade=True,
            ),
        ),
        Espaco(
            nome="Sala de Reuniões Administrativa",
            tipo=TipoEspaco.sala_reuniao,
            capacidade=10,
            descricao="Sala de reuniões da administração",
            andar=1,
            ativo=False,
            unidade_id=unidade_administrativa.id,
            infraestrutura=InfraestruturaEspaco(
                possui_projetor=True,
            ),
        ),
    ]

    espacos_cadastrados = session.exec(
        select(Espaco)
    ).all()

    nomes_existentes = {
        espaco.nome for espaco in espacos_cadastrados
    }

    for espaco in espacos:
        if espaco.nome not in nomes_existentes:
            session.add(espaco)

    session.commit()


def main() -> None:
    with Session(engine) as session:
        popular_unidades(session)
        popular_usuarios(session)
        popular_recursos(session)
        popular_espacos(session)


if __name__ == "__main__":
    main()
