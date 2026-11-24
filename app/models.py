from datetime import datetime
from enum import Enum
from pydantic import field_validator
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


class TipoEspaco(str, Enum):
    sala_reuniao = "sala_reuniao"
    auditorio = "auditorio"
    laboratorio = "laboratorio"
    sala_treinamento = "sala_treinamento"
    multiuso = "multiuso"


class StatusReserva(str, Enum):
    confirmada = "confirmada"
    em_andamento = "em_andamento"
    cancelada = "cancelada"
    concluida = "concluida"


class MetadadosPaginacao(SQLModel):
    total_itens: int
    total_paginas: int
    pagina_atual: int
    tamanho_pagina: int


class ReservaRecurso(SQLModel, table=True):
    reserva_id: int | None = Field(
        default=None, foreign_key="reserva.id", primary_key=True
    )
    recurso_id: int | None = Field(
        default=None, foreign_key="recurso.id", primary_key=True
    )


class UnidadeBase(SQLModel):
    nome: str = Field(index=True)
    endereco: str
    predio: str | None = None
    ativa: bool = True


class Unidade(UnidadeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    espacos: list["Espaco"] = Relationship(back_populates="unidade")


class UnidadeCreate(UnidadeBase):
    pass


class UnidadePublic(UnidadeBase):
    id: int


class UnidadeUpdate(SQLModel):
    nome: str | None = None
    endereco: str | None = None
    predio: str | None = None
    ativa: bool | None = None


class PaginaUnidades(SQLModel):
    dados: list[UnidadePublic]
    paginacao: MetadadosPaginacao


class InfraestruturaBase(SQLModel):
    possui_projetor: bool = False
    possui_som: bool = False
    qtd_computadores: int = Field(default=0, ge=0)
    acessibilidade: bool = False
    climatizado: bool = True
    observacoes: str | None = None


class InfraestruturaEspaco(InfraestruturaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    espaco_id: int = Field(foreign_key="espaco.id", unique=True)
    espaco: "Espaco" = Relationship(back_populates="infraestrutura")


class InfraestruturaCreate(InfraestruturaBase):
    pass


class InfraestruturaPublic(InfraestruturaBase):
    id: int


class InfraestruturaUpdate(SQLModel):
    possui_projetor: bool | None = None
    possui_som: bool | None = None
    qtd_computadores: int | None = None
    acessibilidade: bool | None = None
    climatizado: bool | None = None
    observacoes: str | None = None


class EspacoBase(SQLModel):
    nome: str = Field(index=True)
    tipo: TipoEspaco
    capacidade: int = Field(gt=0)
    descricao: str | None = None
    ativo: bool = True
    andar: int | None = None
    unidade_id: int = Field(foreign_key="unidade.id")


class Espaco(EspacoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    unidade: Unidade | None = Relationship(back_populates="espacos")
    infraestrutura: InfraestruturaEspaco | None = Relationship(
        back_populates="espaco",
        sa_relationship_kwargs={"uselist": False},
    )
    reservas: list["Reserva"] = Relationship(back_populates="espaco")
    bloqueios: list["BloqueioEspaco"] = Relationship(back_populates="espaco")


class EspacoCreate(EspacoBase):
    infraestrutura: InfraestruturaCreate | None = None


class EspacoPublic(EspacoBase):
    id: int


class EspacoPublicDetalhado(EspacoPublic):
    unidade: UnidadePublic | None = None
    infraestrutura: InfraestruturaPublic | None = None


class EspacoUpdate(SQLModel):
    nome: str | None = None
    tipo: TipoEspaco | None = None
    capacidade: int | None = None
    descricao: str | None = None
    ativo: bool | None = None
    andar: int | None = None
    unidade_id: int | None = None
    infraestrutura: InfraestruturaUpdate | None = None


class PaginaEspacos(SQLModel):
    dados: list[EspacoPublicDetalhado]
    paginacao: MetadadosPaginacao


class UsuarioBase(SQLModel):
    nome: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    matricula: str = Field(unique=True, index=True)
    departamento: str
    ativo: bool = True


class Usuario(UsuarioBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reservas: list["Reserva"] = Relationship(back_populates="usuario")


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioPublic(UsuarioBase):
    id: int


class UsuarioUpdate(SQLModel):
    nome: str | None = None
    email: str | None = None
    matricula: str | None = None
    departamento: str | None = None
    ativo: bool | None = None


class PaginaUsuarios(SQLModel):
    dados: list[UsuarioPublic]
    paginacao: MetadadosPaginacao


class RecursoBase(SQLModel):
    nome: str = Field(index=True)
    patrimonio: str = Field(unique=True, index=True)
    categoria: str
    disponivel: bool = True


class Recurso(RecursoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reservas: list["Reserva"] = Relationship(
        back_populates="recursos", link_model=ReservaRecurso
    )


class RecursoCreate(RecursoBase):
    pass


class RecursoPublic(RecursoBase):
    id: int


class RecursoUpdate(SQLModel):
    nome: str | None = None
    patrimonio: str | None = None
    categoria: str | None = None
    disponivel: bool | None = None


class PaginaRecursos(SQLModel):
    dados: list[RecursoPublic]
    paginacao: MetadadosPaginacao


class ReservaBase(SQLModel):
    finalidade: str
    qtd_participantes: int = Field(gt=0)
    data_inicio: datetime = Field(sa_type=DateTime)
    data_fim: datetime = Field(sa_type=DateTime)
    status: StatusReserva = StatusReserva.confirmada
    usuario_id: int = Field(foreign_key="usuario.id")
    espaco_id: int = Field(foreign_key="espaco.id")

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def remover_fuso(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=None)


class Reserva(ReservaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    usuario: Usuario | None = Relationship(back_populates="reservas")
    espaco: Espaco | None = Relationship(back_populates="reservas")
    recursos: list[Recurso] = Relationship(
        back_populates="reservas", link_model=ReservaRecurso
    )


class ReservaCreate(ReservaBase):
    recurso_ids: list[int] = []


class ReservaPublic(ReservaBase):
    id: int


class ReservaPublicDetalhada(ReservaPublic):
    usuario: UsuarioPublic | None = None
    espaco: EspacoPublic | None = None
    recursos: list[RecursoPublic] = []


class ReservaUpdate(SQLModel):
    finalidade: str | None = None
    qtd_participantes: int | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    status: StatusReserva | None = None
    espaco_id: int | None = None
    recurso_ids: list[int] | None = None

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def remover_fuso(cls, v: datetime | None) -> datetime | None:
        return v.replace(tzinfo=None) if v else None


class PaginaReservas(SQLModel):
    dados: list[ReservaPublicDetalhada]
    paginacao: MetadadosPaginacao


class BloqueioBase(SQLModel):
    motivo: str
    data_inicio: datetime = Field(sa_type=DateTime)
    data_fim: datetime = Field(sa_type=DateTime)
    espaco_id: int = Field(foreign_key="espaco.id")

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def remover_fuso(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=None)


class BloqueioEspaco(BloqueioBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    espaco: Espaco | None = Relationship(back_populates="bloqueios")


class BloqueioCreate(BloqueioBase):
    pass


class BloqueioPublic(BloqueioBase):
    id: int


class BloqueioPublicDetalhado(BloqueioPublic):
    espaco: EspacoPublic | None = None


class BloqueioUpdate(SQLModel):
    motivo: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    espaco_id: int | None = None

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def remover_fuso(cls, v: datetime | None) -> datetime | None:
        return v.replace(tzinfo=None) if v else None


class PaginaBloqueios(SQLModel):
    dados: list[BloqueioPublicDetalhado]
    paginacao: MetadadosPaginacao

class HistoricoUtilizacaoPublic(SQLModel):
    reserva_id: int
    finalidade: str
    qtd_participantes: int
    data_inicio: datetime
    data_fim: datetime
    status: StatusReserva
    espaco: str
    unidade: str
    usuario: str

class EspacosMaisRequisitadosPublic(SQLModel):
    espaco_id: int
    espaco: str
    total_reservas: int
