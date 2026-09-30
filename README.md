# Sistema de Recomendação Comercial

Aplicação React + FastAPI + PostgreSQL para acompanhar vendas e oportunidades do escritório de representação. O frontend usa a API real, com autenticação JWT.

- Dashboard com filtros de mês e vendedor, faturamento, pedidos, clientes, ticket, produtos e fábricas.
- Cliente 360º com histórico, ciclos de compra, comparação com a média habitual, mix recomendado e agrupamento por rede.
- Central de alertas de segundo pedido, inatividade de cliente/fábrica e abandono de produtos.
- Importação transacional de duas planilhas e histórico das cargas.
- Aprovação de usuários pela área administrativa.

Pedidos diretos de fábrica sem itens são válidos: participam do faturamento e da atividade do cliente/fábrica. Recomendações de produtos utilizam apenas itens conhecidos.

## Executar localmente

Requisitos: Python 3.11/3.12, Node.js 22.12+ e banco PostgreSQL. Na raiz:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o arquivo local `.env` com a conexão, chaves e credenciais iniciais. Não versionar este arquivo. As chaves devem ser preservadas entre as implantações para manter a leitura dos dados criptografados.

```powershell
cd frontend
npm ci
npm run build
cd ..
./.venv/Scripts/python.exe start.py
```

Abra http://localhost:8000. O startup aplica migrações e cria o administrador indicado por `ADMIN_EMAIL` e `ADMIN_PASSWORD`, caso ele ainda não exista. Cadastros novos aguardam aprovação em **Usuários**.

Para desenvolver a interface, execute `npm run dev` em `frontend` com a API na porta 8000. O Vite encaminha `/api` à API local.

## Implantação e operação

Veja [o guia do Neon e Render](docs/IMPLANTACAO.md). O Dockerfile compila o frontend e publica interface e API no mesmo serviço. `render.yaml` oferece uma configuração Blueprint alternativa.

## Verificar

```powershell
./.venv/Scripts/python.exe -m pytest tests -q
cd frontend
npm run lint
npm run build
```

Os testes usam SQLite isolado e não alteram o Neon. Para conferir a cadeia de migrações no PostgreSQL, `python scripts/verificar_migracoes.py` cria um esquema temporário e desfaz a transação ao final.
