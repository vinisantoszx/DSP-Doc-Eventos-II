# Sistema de Reservas de Espaços

Trabalho Prático 2 da disciplina de Desenvolvimento de Software para Persistência, da UFC Quixadá. O projeto consiste em uma API para administrar espaços físicos de uma instituição, organizando seus horários de utilização, os usuários responsáveis pelas reservas e os recursos necessários para cada atividade.

A proposta utiliza o Tema 6: Sistema de Reservas de Espaços. Além do cadastro dos ambientes, o sistema considera situações como conflitos de horários, períodos de manutenção e disponibilidade de equipamentos compartilhados.

## Equipe

O desenvolvimento foi dividido entre os integrantes para que cada parte pudesse ser trabalhada em paralelo:

- Chrystian: estrutura inicial, unidades, espaços, infraestrutura e consulta de disponibilidade.
- Vinícius: usuários, recursos móveis e operações de reservas.
- Sebastian: bloqueios de espaços, relatórios, estatísticas, migrações, povoamento do banco e documentação.

## Tecnologias

A API foi desenvolvida em Python com FastAPI e SQLModel. O SQLAlchemy é utilizado na comunicação com o banco, enquanto o Alembic controla as alterações na estrutura das tabelas.

O projeto pode trabalhar com PostgreSQL ou SQLite. A escolha é feita pela variável de ambiente `DATABASE_URL`, sem precisar modificar os modelos para trocar de banco.

## Como os dados estão organizados

O modelo foi pensado a partir das relações que existem no processo de reserva. Uma unidade pode possuir vários espaços; cada espaço tem sua própria ficha de infraestrutura e pode receber reservas em horários diferentes. Os usuários registram as reservas, que podem utilizar equipamentos cadastrados no sistema.

As entidades principais são:

| Entidade | Finalidade |
|---|---|
| Unidade | Identifica uma unidade institucional |
| Espaco | Guarda os dados dos ambientes disponíveis |
| InfraestruturaEspaco | Registra os recursos físicos de cada espaço |
| Usuario | Armazena os dados de quem realiza as reservas |
| Recurso | Representa equipamentos que podem ser utilizados em diferentes ambientes |
| Reserva | Registra a finalidade, o período e os participantes de uma utilização |
| BloqueioEspaco | Representa períodos em que um ambiente não pode ser reservado |

Além dessas entidades, existe a tabela associativa `ReservaRecurso`, responsável por relacionar reservas e equipamentos.

### Relacionamentos

- Uma `Unidade` pode possuir vários `Espaco` (1:N).
- Um `Espaco` possui uma ficha de `InfraestruturaEspaco` (1:1).
- Um `Usuario` pode realizar várias `Reserva` (1:N).
- Um `Espaco` pode aparecer em várias `Reserva` (1:N).
- Um `Espaco` pode possuir vários `BloqueioEspaco` (1:N).
- Uma `Reserva` pode utilizar vários `Recurso`, e um recurso pode aparecer em reservas diferentes (N:N).

No relacionamento N:N, a tabela `ReservaRecurso` utiliza `reserva_id` e `recurso_id` como chave primária composta.

### Diagrama do modelo

```mermaid
erDiagram
    UNIDADE ||--o{ ESPACO : possui
    ESPACO ||--o| INFRAESTRUTURA_ESPACO : possui
    USUARIO ||--o{ RESERVA : realiza
    ESPACO ||--o{ RESERVA : recebe
    ESPACO ||--o{ BLOQUEIO_ESPACO : possui
    RESERVA ||--o{ RESERVA_RECURSO : utiliza
    RECURSO ||--o{ RESERVA_RECURSO : associado

    UNIDADE {
        int id PK
        string nome
        string endereco
        string predio
        boolean ativa
    }

    ESPACO {
        int id PK
        string nome
        string tipo
        int capacidade
        int andar
        int unidade_id FK
    }

    INFRAESTRUTURA_ESPACO {
        int id PK
        int espaco_id FK
        boolean possui_projetor
        boolean possui_som
        int qtd_computadores
        boolean acessibilidade
        boolean climatizado
    }

    USUARIO {
        int id PK
        string nome
        string email
        string matricula
        string departamento
        boolean ativo
    }

    RECURSO {
        int id PK
        string nome
        string patrimonio
        string categoria
        boolean disponivel
    }

    RESERVA {
        int id PK
        string finalidade
        int qtd_participantes
        datetime data_inicio
        datetime data_fim
        string status
        int usuario_id FK
        int espaco_id FK
    }

    BLOQUEIO_ESPACO {
        int id PK
        string motivo
        datetime data_inicio
        datetime data_fim
        int espaco_id FK
    }

    RESERVA_RECURSO {
        int reserva_id PK, FK
        int recurso_id PK, FK
    }
```

As reservas possuem quatro situações possíveis: `confirmada`, `em_andamento`, `cancelada` e `concluida`.

## Preparando o ambiente

É necessário ter Python e Git instalados. Para trabalhar com PostgreSQL, também é preciso ter uma instância do banco disponível. Quem preferir testar localmente pode começar com SQLite.

Clone o repositório e entre na pasta:

```bash
git clone [https://github.com/vinisantoszx/DSP-Doc-Eventos-II.git](https://github.com/vinisantoszx/DSP-Doc-Eventos-II.git)
cd DSP-Doc-Eventos-II
```

Crie o ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instale as bibliotecas utilizadas:

```bash
pip install -r requirements.txt
```

## Escolhendo o banco de dados

A configuração da conexão fica em um arquivo `.env`, criado na raiz do projeto. O módulo `app/database.py` carrega essa variável e cria a conexão utilizada pelas sessões da aplicação.

Para começar com SQLite, basta usar:

```env
DATABASE_URL=sqlite:///./reservas.db
```

Nesse caso, o arquivo `reservas.db` será criado no próprio projeto.

Para PostgreSQL, primeiro crie um banco chamado `reservas_espacos`. Depois, configure a conexão no `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:SUA_SENHA@localhost:5432/reservas_espacos
```

Troque `SUA_SENHA` pela senha do usuário configurado no PostgreSQL.

O arquivo `.env` não deve ser enviado ao Git, pois contém configurações locais. Ele já está listado no `.gitignore`.

## Atualizações da estrutura com Alembic

As tabelas são definidas pelos modelos de `app/models.py`. Quando a estrutura muda, o Alembic permite registrar essa alteração em uma migração, em vez de depender de alterações manuais no banco.

A configuração fica em `migrations/env.py`, que utiliza o `SQLModel.metadata` e a mesma variável `DATABASE_URL` da aplicação.

Com o banco escolhido e o `.env` configurado, aplique as migrações **antes de iniciar o servidor pela primeira vez**:

```bash
alembic upgrade head
```

Para consultar a revisão aplicada ao banco:

```bash
alembic current
```

Para consultar a revisão mais recente disponível:

```bash
alembic heads
```

Quando um modelo receber uma alteração estrutural, uma nova revisão pode ser criada com:

```bash
alembic revision --autogenerate -m "descricao da alteracao"
```

Em seguida, aplique a alteração:

```bash
alembic upgrade head
```

No desenvolvimento deste projeto foram criadas duas revisões: a primeira monta as tabelas iniciais; a segunda acrescenta o campo `andar` à tabela `espaco`.

## Inserindo os dados de exemplo

O arquivo `scripts/seed.py` prepara registros para facilitar os testes da API. Ele utiliza `Session(engine)` e os próprios modelos do projeto para inserir os dados diretamente no banco.

Para executar:

```bash
python -m scripts.seed
```

O conjunto de dados preparado contém:

| Tipo de registro | Quantidade |
|---|---:|
| Unidades | 3 |
| Usuários | 5 |
| Recursos | 5 |
| Espaços | 8 |
| Reservas | 12 |
| Bloqueios | 4 |

As reservas de exemplo contemplam os quatro status do sistema e relacionam usuários, espaços e recursos. Os espaços também recebem registros de infraestrutura, e alguns ambientes possuem bloqueios em períodos específicos.

O seed evita duplicar vários dos registros quando executado novamente. Há uma particularidade nas reservas: se já existir pelo menos uma reserva cadastrada, o script não insere novamente o conjunto de reservas de exemplo.

## Iniciando a API

Depois de configurar o banco e aplicar as migrações, inicie o servidor:

```bash
uvicorn app.main:app --reload
```

A aplicação ficará disponível em `http://127.0.0.1:8000`.

A documentação interativa pode ser acessada pelo Swagger:

`http://127.0.0.1:8000/docs`

Também existe a documentação ReDoc:

`http://127.0.0.1:8000/redoc`

O endereço principal (`GET /`) retorna `{"status": "ativo", "sistema": "Sistema de Reservas de Espaços"}`. Durante as requisições, o middleware registra o método HTTP, o caminho, o código de resposta e o tempo de processamento.

## Paginação e filtros

Todas as listagens principais (`GET /unidades/`, `GET /espacos/`, `GET /usuarios/`, `GET /recursos/`, `GET /reservas/` e `GET /bloqueios/`) executam paginação e filtragem diretamente no banco de dados via SQLAlchemy/SQLModel:

- **Paginação:** controlada pelos parâmetros `pagina` (padrão `1`) e `tamanho_pagina` (padrão `10`, máximo `100`), retornando a lista em `dados` e os metadados em `paginacao` (`total_itens`, `total_paginas`, `pagina_atual` e `tamanho_pagina`).
- **Filtros combinados:** parâmetros opcionais combinados dinamicamente na cláusula `WHERE` (incluindo buscas parciais com `ILIKE` e junções com tabelas relacionadas).

## Unidades e espaços

### Unidades (`/unidades`)

| Método | Caminho | Operação |
|---|---|---|
| POST | `/unidades/` | Cadastra uma unidade |
| GET | `/unidades/` | Lista unidades (filtros: `nome`, `predio`, `ativa`) |
| GET | `/unidades/{unidade_id}` | Consulta uma unidade |
| GET | `/unidades/{unidade_id}/espacos` | Lista todos os espaços vinculados à unidade (1:N) |
| PATCH | `/unidades/{unidade_id}` | Atualiza parcialmente uma unidade |
| DELETE | `/unidades/{unidade_id}` | Remove uma unidade (retorna HTTP 409 se houver espaços vinculados) |

### Espaços e infraestrutura (`/espacos`)

| Método | Caminho | Operação |
|---|---|---|
| POST | `/espacos/` | Cadastra um espaço junto com sua ficha 1:1 de `InfraestruturaEspaco` |
| GET | `/espacos/` | Lista espaços (filtros: `nome`, `unidade_id`, `tipo`, `andar`, `capacidade_minima`, `ativo`, `possui_projetor`, `possui_som`, `acessibilidade`) |
| GET | `/espacos/disponiveis` | Busca ambientes livres em um intervalo de datas |
| GET | `/espacos/{espaco_id}` | Consulta um espaço com unidade e infraestrutura |
| PATCH | `/espacos/{espaco_id}` | Atualiza parcialmente dados do espaço e/ou de sua infraestrutura |
| DELETE | `/espacos/{espaco_id}` | Remove o espaço ou o desativa (`ativo = false`) caso possua histórico de reservas/bloqueios |

Exemplo de cadastro de espaço com infraestrutura 1:1 (`POST /espacos/`):

```json
{
    "nome": "Laboratório de Redes",
    "tipo": "laboratorio",
    "capacidade": 30,
    "descricao": "Laboratório para aulas práticas",
    "andar": 2,
    "unidade_id": 1,
    "infraestrutura": {
        "possui_projetor": true,
        "possui_som": false,
        "qtd_computadores": 30,
        "acessibilidade": true,
        "climatizado": true
    }
}
```

## Usuários, recursos e reservas

### Usuários (`/usuarios`)

| Método | Caminho | Operação |
|---|---|---|
| POST | `/usuarios/` | Cadastra um usuário (`email` e `matricula` únicos) |
| GET | `/usuarios/` | Lista usuários (filtros: `nome`, `departamento`, `ativo`) |
| GET | `/usuarios/{usuario_id}` | Consulta um usuário |
| GET | `/usuarios/{usuario_id}/reservas` | Lista o histórico paginado de reservas do usuário |
| PATCH | `/usuarios/{usuario_id}` | Atualiza parcialmente um usuário |
| DELETE | `/usuarios/{usuario_id}` | Remove o usuário ou o desativa (`ativo = false`) se houver reservas vinculadas |

### Recursos móveis (`/recursos`)

| Método | Caminho | Operação |
|---|---|---|
| POST | `/recursos/` | Cadastra um recurso (`patrimonio` único) |
| GET | `/recursos/` | Lista recursos (filtros: `nome`, `categoria`, `disponivel`) |
| GET | `/recursos/{recurso_id}` | Consulta um recurso |
| PATCH | `/recursos/{recurso_id}` | Atualiza parcialmente um recurso |
| DELETE | `/recursos/{recurso_id}` | Remove o recurso ou o marca como indisponível (`disponivel = false`) se já usado em reservas |

### Reservas (`/reservas`)

| Método | Caminho | Operação |
|---|---|---|
| POST | `/reservas/` | Cria uma reserva e associa recursos móveis (N:N via `recurso_ids`) |
| GET | `/reservas/` | Lista reservas (filtros: `usuario_id`, `espaco_id`, `recurso_id`, `status`, `inicio`, `fim`) |
| GET | `/reservas/espacos/{espaco_id}` | Consulta o histórico paginado de reservas de um espaço |
| GET | `/reservas/{reserva_id}` | Consulta uma reserva detalhada |
| PATCH | `/reservas/{reserva_id}` | Altera horário, espaço, status ou recursos, revalidando conflitos |
| DELETE | `/reservas/{reserva_id}` | Remove uma reserva e seus vínculos na tabela associativa |

Exemplo de solicitação de reserva (`POST /reservas/`):

```json
{
    "finalidade": "Seminário de Engenharia de Software",
    "qtd_participantes": 40,
    "data_inicio": "2026-12-05T14:00:00",
    "data_fim": "2026-12-05T16:00:00",
    "usuario_id": 1,
    "espaco_id": 1,
    "recurso_ids": [1, 2]
}
```

## Bloqueios de espaços

O módulo de bloqueios permite registrar períodos de manutenção, limpeza ou reforma. A ideia é impedir que um ambiente seja bloqueado em um horário que já esteja reservado.

As rotas deste módulo são:

| Método | Caminho | Operação |
|---|---|---|
| POST | `/bloqueios/` | Cria um bloqueio |
| GET | `/bloqueios/` | Lista os bloqueios |
| GET | `/bloqueios/{bloqueio_id}` | Consulta um bloqueio |
| PATCH | `/bloqueios/{bloqueio_id}` | Altera um bloqueio |
| DELETE | `/bloqueios/{bloqueio_id}` | Remove um bloqueio |

Na listagem, os parâmetros `pagina` e `tamanho_pagina` controlam a paginação. Também é possível filtrar pelo `espaco_id` e por um intervalo de datas usando `inicio` e `fim`.

Um exemplo de cadastro é:

```json
{
    "motivo": "Manutenção dos equipamentos",
    "data_inicio": "2026-12-01T08:00:00",
    "data_fim": "2026-12-01T12:00:00",
    "espaco_id": 1
}
```

A data final precisa ser posterior à inicial e o espaço informado deve existir. Caso haja uma reserva confirmada ou em andamento que se sobreponha ao período, a operação é recusada com HTTP 409. Espaços inexistentes e bloqueios não encontrados retornam HTTP 404.

## Relatórios

Os relatórios estão agrupados sob o prefixo `/relatorios`. Foram implementadas quatro consultas, cada uma voltada a uma visão diferente da utilização dos ambientes.

### Histórico de utilização

`GET /relatorios/historico-utilizacao`

A consulta reúne dados de reservas, espaços, unidades e usuários. Pode receber três filtros opcionais:

| Parâmetro | O que faz |
|---|---|
| `data_inicio` | Define o início do período |
| `data_fim` | Define o fim do período |
| `unidade_id` | Restringe os resultados a uma unidade |

O período considera reservas que tenham alguma sobreposição com o intervalo informado. Por exemplo, uma reserva que começou antes da data inicial, mas terminou dentro do período, também pode aparecer no resultado.

Quando as duas datas são informadas, `data_fim` precisa ser posterior a `data_inicio`.

Exemplo de consulta:

```http
GET /relatorios/historico-utilizacao?data_inicio=2026-11-25T00:00:00&data_fim=2026-11-28T00:00:00&unidade_id=2
```

Cada item retornado apresenta o identificador da reserva, finalidade, participantes, datas, status, espaço, unidade e usuário responsável.

### Espaços mais requisitados

`GET /relatorios/espacos-mais-requisitados`

O resultado apresenta os espaços ordenados pela quantidade de reservas. A contagem é feita no banco com agregação e agrupamento por espaço.

A consulta não exige parâmetros. Espaços que ainda não receberam reservas também aparecem, com total igual a zero.

### Reservas por unidade

`GET /relatorios/reservas-por-unidade`

Mostra quantas reservas estão relacionadas a cada unidade institucional. Para chegar ao resultado, a consulta relaciona unidades, espaços e reservas, agrupando os registros por unidade.

Também não exige parâmetros. Unidades sem reservas são mantidas no resultado.

### Estatísticas gerais

`GET /relatorios/estatisticas-gerais`

Essa rota retorna quatro totais: reservas futuras, em andamento, canceladas e concluídas. Para o cálculo de futuras, são consideradas as reservas confirmadas cuja data de início ainda não chegou. As demais categorias seguem os status registrados no sistema.

O retorno inclui ainda uma relação dos recursos associados às reservas, em ordem decrescente de quantidade. Essa contagem considera os vínculos da tabela `ReservaRecurso`, inclusive aqueles associados a reservas canceladas.

A consulta não recebe parâmetros.

## Consulta de espaços disponíveis — Tema 6

A funcionalidade central do Tema 6 é a busca por ambientes que atendam às condições de uma atividade em determinado período, implementada em:

`GET /espacos/disponiveis`

Parâmetros aceitos pela consulta:

| Parâmetro | Finalidade |
|---|---|
| `data_inicio` | Início do período desejado (obrigatório) |
| `data_fim` | Fim do período desejado (obrigatório) |
| `qtd_participantes` | Quantidade mínima de pessoas que utilizarão o ambiente (padrão `1`) |
| `unidade_id` | Filtra por uma unidade específica |
| `tipo` | Filtra pelo tipo de espaço (`sala_reuniao`, `auditorio`, `laboratorio`, `sala_treinamento`, `multiuso`) |
| `andar` | Filtra pelo andar do ambiente |
| `possui_projetor` | Filtra espaços com projetor fixo (`true` / `false`) |
| `possui_som` | Filtra espaços com sistema de som (`true` / `false`) |
| `acessibilidade` | Filtra espaços com acessibilidade (`true` / `false`) |

A busca combina informações de `Espaco`, `Unidade` e `InfraestruturaEspaco` com subconsultas sobre `Reserva` e `BloqueioEspaco`. Ambientes inativos, vinculados a unidades inativas, com capacidade inferior à solicitada ou que possuam reservas ativas (`confirmada` ou `em_andamento`) ou bloqueios sobrepostos ao intervalo são excluídos diretamente na consulta SQL.

Exemplo de consulta:

```http
GET /espacos/disponiveis?data_inicio=2026-12-05T14:00:00&data_fim=2026-12-05T16:00:00&qtd_participantes=20&possui_projetor=true
```

## Regras de negócio consideradas

As validações do sistema preservam a consistência dos horários, dos relacionamentos e do histórico de utilização:

- A data final de uma reserva, bloqueio ou consulta deve ser posterior à data inicial.
- O usuário, o espaço e os recursos referenciados precisam existir e estar ativos/disponíveis.
- A quantidade de participantes não pode ultrapassar a capacidade do ambiente.
- Reservas `confirmada` ou `em_andamento` não podem ocupar o mesmo espaço em períodos sobrepostos (intervalos adjacentes, como 14h–16h e 16h–18h, são permitidos).
- Uma reserva não pode coincidir com um bloqueio de manutenção, limpeza ou reforma.
- Um recurso móvel não pode ser utilizado em duas reservas ativas simultâneas.
- Alterações de reservas (`PATCH`) repetem as validações de disponibilidade, capacidade e conflitos, desconsiderando a própria reserva editada.
- Um bloqueio não pode ser criado ou atualizado sobre uma reserva `confirmada` ou `em_andamento`.
- O histórico de reservas é preservado: ao excluir um espaço, usuário ou recurso que já possua reservas associadas, o registro é apenas desativado (`ativo = false` ou `disponivel = false`) em vez de ser apagado do banco.
- Uma unidade não pode ser excluída caso possua espaços vinculados (HTTP 409).

Nas respostas da API são utilizados códigos HTTP como `200`, `201`, `204`, `400`, `404`, `409` e `422`, conforme o resultado da operação ou o tipo de problema encontrado.

## Organização dos arquivos

O código está separado por responsabilidade. Os modelos e a conexão com o banco ficam em `app/`, enquanto as rotas estão organizadas dentro de `app/routers/`.

```text
DSP-Doc-Eventos-II/
│
├── app/
│   ├── routers/
│   │   ├── bloqueios.py
│   │   ├── espacos.py
│   │   ├── recursos.py
│   │   ├── relatorios.py
│   │   ├── reservas.py
│   │   ├── unidades.py
│   │   └── usuarios.py
│   │
│   ├── database.py
│   ├── main.py
│   └── models.py
│
├── migrations/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── scripts/
│   └── seed.py
│
├── .env
├── .gitignore
├── alembic.ini
├── README.md
└── requirements.txt
```

O `main.py` registra os roteadores, o middleware de log e configura a aplicação FastAPI. `database.py` concentra a conexão e a criação das sessões. Os modelos de tabelas e os schemas de entrada e saída ficam em `models.py`.

---
Trabalho Prático 2 — Desenvolvimento de Software para Persistência
UFC Quixadá