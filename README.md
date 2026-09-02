# Sistema de Recomendação e Dashboard Gerencial (TCC)

## 🎯 Sobre o Projeto
Este repositório contém o desenvolvimento de um sistema de suporte à decisão voltado para **representantes comerciais e vendedores internos** do setor de representação comercial no segmento de material de construção, elétrico e agorpecuário.

O sistema integra análise de dados, inteligência artificial e visualização de indicadores (KPIs) para otimizar o processo de vendas, sugerir produtos estratégicos e monitorar o desempenho por região, cliente e linha de produto.

---

## 🛠 Tecnologias e Ferramentas
* **Linguagens:** Python.
* **Frameworks:** FastAPI.
* **Banco de Dados:** PostgreSQL.
* **ORM:** SQLAlchemy.
* **Gestão:** Git, GitHub Projects.
* **Processamento:** Pandas e Scikit-learn.
* **UI/UX:** .
* **Comunicação:** REST API.
* **Ambiente:** VS Code.
* **Autentificação:** JWT (JSON Web Tokens).

---

## 👥 Colaboradores
* **Ricardo Nilson Klug**
* **Rafael Júlio Klug**

## 📊 Funcionalidades
- **Dashboard Gerencial:** Visualização centralizada de vendas, metas e indicadores de performance.
- **Motor de Recomendação:** Algoritmo de filtragem para sugestão inteligente de produtos (*Cross-selling*).
- **Gestão de Avisos:** Alertas automáticos sobre comportamento de consumo e oportunidades de negócio.
- **Relatórios Dinâmicos:** Filtros detalhados por região, cliente e categoria de produto.

---

## 📂 Estrutura do Repositório
```text
/
├── .github/                # Configurações do GitHub (Issues, Projects)
├── .vscode/                # Configurações do editor (ignorada pelo Git)
├── data/                   # Gestão de dados do sistema
│   ├── raw/                # Dados brutos (.csv, .xlsx)
│   ├── processed/          # Dados tratados pela IA
│   ├── scripts/            # Scripts de limpeza (Python)
│   └── README.md           # Documentação da camada de dados
├── docs/                   # Documentação técnica e UML
├── frontend/               # Pasta dedicada ao (UI/UX)
├── src/                    # Código fonte do sistema
│   └── backend/            # Lógica do motor de IA e API
│       ├── app/            # Código da aplicação
│       │   ├── api/        # Endpoints (rotas para o front)
│       │   ├── core/       # database.py, config.py, segurança
│       │   ├── models/     # Classes do banco (SQLAlchemy)
│       │   ├── schemas/    # Validação (Pydantic)
│       │   └── services/   # Lógica da IA/Recomendação
│       ├── main.py         # Ponto de entrada
│       └── requirements.txt # Bibliotecas do projeto
├── .env                    # Variáveis sensíveis
├── .env.example            # Modelo de variáveis de ambiente
├── .gitignore              # Lista de arquivos ignorados
└── README.md               # Documentação principal e tecnologias


