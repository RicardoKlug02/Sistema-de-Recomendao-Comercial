# Sistema de Recomendação e Dashboard Gerencial (TCC)

Sistema de suporte à decisão para representantes comerciais e vendedores internos dos segmentos de materiais de construção, elétrico e agropecuário. O projeto busca reunir indicadores de vendas e recomendações de produtos para apoiar o acompanhamento de clientes e a identificação de oportunidades comerciais.

## Estado atual

O frontend já permite navegar do login ao dashboard, baseado nos wireframes da pasta `docs`.

| Recurso | Situação |
| --- | --- |
| Dashboard | Quatro indicadores, faturamento mensal, vendas por categoria, principais clientes, últimas importações e oportunidades recentes. Dados demonstrativos. |
| Menu e cards | Componentes reutilizáveis; o menu navega às seções do próprio painel. |
| Detalhes das oportunidades | Diálogo com cliente, produto, relevância e valor estimado. |
| Importação | Seleção ou arraste de XLS/XLSX até 10 MB, resultado simulado, detalhes e histórico paginado. Sem envio ao backend. |
| Backend | Estrutura inicial em FastAPI, modelos de dados e serviço de importação de planilhas. Ainda não integrado ao frontend. |

A tela completa de clientes, a autenticação real, o motor de recomendação, os alertas e os relatórios com filtros estão previstos para as próximas etapas. JWT ainda não está implementado.

## Tecnologias

- **Frontend:** JavaScript, React 19, Vite 8, HTML e CSS; ESLint para análise do código.
- **Backend:** Python e FastAPI; Pydantic para os esquemas de dados.
- **Persistência:** PostgreSQL e SQLAlchemy, com estrutura inicial de migrações em Alembic.
- **Importação e tratamento de dados:** Pandas.
- **Testes do backend:** Pytest.

O dashboard utiliza recursos nativos de HTML e CSS para os gráficos, sem bibliotecas adicionais de visualização.

## Executar o frontend

É possível testar a interface sem iniciar o backend ou configurar o banco de dados.

**Pré-requisitos:** Node.js 20.19+ da versão 20 ou Node.js 22.12+ e npm, conforme a versão do Vite utilizada.

Na raiz do repositório:

```bash
cd frontend
npm ci
npm run dev
```

Acesse o endereço informado pelo Vite, normalmente [http://localhost:5173](http://localhost:5173).

Para demonstrar o fluxo, informe qualquer e-mail válido e uma senha não vazia. O login abre o dashboard; “Sair da conta” retorna à autenticação. Senhas e tokens não são persistidos.

Na pasta `frontend`, os comandos de verificação são:

```bash
npm run lint
npm run build
```

A compilação gera os arquivos de produção em `frontend/dist`. Consulte o [README do frontend](frontend/README.md) para conhecer os componentes, suas responsabilidades e o roteiro de conferência manual.

## Backend em desenvolvimento

O ponto de entrada é `src/backend/main.py`. Atualmente, ele expõe a rota inicial `GET /`; as rotas comerciais ainda não estão registradas na aplicação.

O arquivo `src/backend/requirements.txt` ainda está vazio. Para executar apenas a API inicial, crie um ambiente virtual e instale as dependências mínimas, a partir da raiz:

```bash
python -m venv .venv
```

Ative o ambiente no macOS/Linux:

```bash
source .venv/bin/activate
```

Ou no PowerShell do Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Em seguida:

```bash
python -m pip install fastapi uvicorn
python -m uvicorn src.backend.main:app --reload
```

A API fica disponível em [http://localhost:8000](http://localhost:8000), com documentação interativa em [http://localhost:8000/docs](http://localhost:8000/docs).

Essa instalação mínima não cobre os módulos de banco e importação. Para integrá-los, ainda é necessário consolidar as dependências no `requirements.txt`, configurar o PostgreSQL e revisar as migrações. O arquivo `.env.example` contém o modelo das variáveis de ambiente: copie-o para `.env` na raiz e preencha os campos `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` ao configurar a persistência. `SECRET_KEY` está reservado para a autenticação futura.

## Estrutura do repositório

```text
.
├── .github/                 # Configurações e automação do GitHub
├── alembic/                 # Estrutura inicial de migrações
├── alembic.ini              # Configuração do Alembic
├── data/                    # Dados e documentação do tratamento
├── docs/                    # Requisitos e wireframes das telas
├── frontend/
│   ├── public/              # Recursos estáticos
│   ├── src/
│   │   ├── componentes/     # Menu, cards e campos reutilizáveis
│   │   ├── paginas/         # Dashboard comercial e seus estilos
│   │   ├── servicos/        # Autenticação simulada e dados do painel
│   │   ├── Aplicacao.jsx    # Fluxo de autenticação e sessão
│   │   └── main.jsx         # Inicialização do React
│   └── README.md            # Documentação específica da interface
├── scripts/                 # Utilitários de inicialização do banco
├── src/backend/
│   ├── app/
│   │   ├── api/             # Definições de rotas
│   │   ├── core/            # Configuração do banco
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Esquemas Pydantic
│   │   └── services/        # Serviço de importação de planilhas
│   ├── main.py              # Aplicação FastAPI
│   └── requirements.txt     # Dependências a consolidar
├── tests/                   # Testes Python existentes
├── .env.example             # Modelo de configuração local
└── README.md
```

Os componentes, funções e serviços próprios do frontend utilizam nomes em português, com responsabilidades descritas no README dessa camada. Propriedades nativas de React e HTML mantêm os nomes exigidos pelas tecnologias.

## Referências visuais

- [Tela de login](docs/Tela%20de%20login.png)
- [Wireframe do dashboard](docs/wireframe_dashboard.png)
- [Wireframe de clientes](docs/wireframe_cliente.png)
- [Wireframe de importação](docs/wireframe_importacao.png)
- [Documentação da camada de dados](data/README.md)

## Colaboradores

- Ricardo Nilson Klug
- Rafael Júlio Klug
