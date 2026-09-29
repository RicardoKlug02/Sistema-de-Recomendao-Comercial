<<<<<<< Updated upstream
# Sistema de Recomendação Comercial — Rio Verde

Sistema de suporte à decisão para representantes comerciais, com acompanhamento de clientes, alertas de recompra e recomendações baseadas no histórico da carteira.
=======
# Rio Verde — Inteligência Comercial

Aplicação React e FastAPI para consultar a carteira de clientes, acompanhar compras e identificar oportunidades. A interface utiliza a API real; não aceita credenciais fictícias nem simula importações.
>>>>>>> Stashed changes

## Telas disponíveis

<<<<<<< Updated upstream
O frontend está conectado à API hospedada no Render: [documentação interativa](https://sistema-de-recomendao-comercial.onrender.com/docs).

| Recurso | Implementação |
| --- | --- |
| Autenticação | Login real com token Bearer e contas ativas/aprovadas. Sessão mantida na aba; expiração retorna ao login. |
| Visão geral | Cartões de alertas de recompra com busca, prioridade e tipo. Indicadores calculados somente sobre os até 50 alertas retornados. |
| Clientes | Busca real por razão social, nome fantasia ou documento; cartões com acesso ao perfil. |
| Cliente 360° | Comparação de faturamento, ciclos por fábrica, reposição, abandono e sugestões de expansão de mix. |
| Produtos complementares | Consulta de produtos comprados em conjunto, a partir de itens escolhidos no perfil. |
| Importação | Envio real de duas planilhas XLS/XLSX ao backend, disponível para administradores e gestores. Atualiza as consultas após confirmação. |
| Aparência | Tema claro, verde suave, logo Rio Verde e componentes responsivos em português. |

A API publicada ainda não expõe indicadores financeiros globais, listagem completa paginada, filtros comerciais globais ou histórico de importações. A interface informa essas limitações e não preenche campos com dados demonstrativos. Não há recomendações de whitespace regional.

## Executar a interface

Requer Node.js compatível com Vite 8: 20.19+ na série 20 ou 22.12+.

```bash
=======
- Login, solicitação de cadastro, recuperação e redefinição de senha.
- Visão geral com faturamento mensal, clientes, pedidos, fábricas e principais compradores.
- Clientes com busca, paginação e acesso direto à ficha em `/#/clientes/123`.
- Ficha individual com identificação, localização, indicadores, situação por fábrica, histórico com itens, reposição, abandono e expansão de mix.
- Oportunidades de venda complementar por seleção de produtos.
- Alertas de recompra calculados sob demanda.
- Relatórios por datas, cliente, categoria, cidade/região e fábrica, com impressão da página atual.
- Importação de duas planilhas, resultado e histórico de cargas para gestores/administradores.
- Administração de usuários, aprovação e controle de perfil.
- Minha conta e alteração de senha com encerramento das sessões anteriores.

O acesso comercial é compartilhado entre os usuários aprovados. Não há segregação de carteira por vendedor. Alertas ainda não são enviados automaticamente, e a tela explicita que a lista é calculada sob consulta. O relatório imprime a página atual, não um documento com todos os resultados.

## Instalação reproduzível local

Pré-requisitos: Python **3.12**, Node **22.14.0** (arquivo `frontend/.nvmrc`), npm e Docker Compose para PostgreSQL. Pode-se utilizar um PostgreSQL 16 já instalado, ajustando `DATABASE_URL`.

Na raiz, macOS/Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/configurar.py
docker compose up -d --wait db
python -m alembic upgrade head
python scripts/criar_usuario.py --email admin@empresa.com --nome "Administrador"
python -m uvicorn src.backend.main:app --reload
```

Windows PowerShell: use `py -3.12 -m venv .venv` e `.venv\Scripts\Activate.ps1`; os demais comandos Python são iguais.

Em outro terminal:

```sh
>>>>>>> Stashed changes
cd frontend
npm ci
npm run dev
```

<<<<<<< Updated upstream
Abra o endereço informado pelo Vite, normalmente `http://localhost:5173`. Entre com uma conta ativa e aprovada da API. Não é necessário iniciar Python ou PostgreSQL para usar o backend do Render.

Em desenvolvimento, as chamadas passam pelo proxy do Vite para o Render. Na produção, a interface usa diretamente a API hospedada. Para substituir a URL, consulte `frontend/.env.example` e reinicie/recompile a interface. Tokens e senhas não devem ser colocados nessas variáveis.

Verificações na pasta `frontend`:

```bash
npm test
=======
Abra [a interface](http://localhost:5173) e entre com o administrador criado. A senha é solicitada de forma oculta pelo utilitário; não existe senha administrativa padrão. [A documentação da API](http://localhost:8000/docs) descreve os endpoints.

`requirements.txt` fixa as dependências diretas e transitivas resolvidas. `requirements.in` registra as dependências diretas. Atualizações devem gerar um novo lock em ambiente limpo e passar pela CI. A instalação do frontend usa `package-lock.json` e `npm ci`.

`scripts/configurar.py` gera chaves aleatórias uma única vez e nunca sobrescreve `.env`. Guarde a chave de criptografia e o segredo do índice de documento junto aos backups; não os regenere em uma base com dados. O banco Docker fica limitado a localhost e utiliza credenciais apenas para desenvolvimento. Para outro banco, ajuste `.env` antes de executar migrações.

O frontend encaminha `/api` para `127.0.0.1:8000` durante o desenvolvimento. Em hospedagem, configure o proxy ou `VITE_API_URL` antes de compilar e permita a origem correta em `CORS_ORIGINS`. A sessão fica em memória e exige novo login após recarregar.

## E-mail

O sistema inicia com `MAIL_ENABLED=False`. Administradores aprovam cadastros pela tela de usuários; recuperação por e-mail informa indisponibilidade enquanto SMTP não estiver configurado.

Para habilitar, configure `MAIL_ENABLED=True`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_FROM`, credenciais/TLS, `ADMIN_EMAIL`, `FRONTEND_URL` e `BACKEND_URL`. O cadastro permanece pendente se o envio falhar e pode ser aprovado na interface. O link de aprovação exibe uma confirmação antes de alterar o acesso; o de recuperação expira em 30 minutos e não pode ser reutilizado depois da troca de senha.

## Importação e integridade

Consulte [o contrato de importação](docs/importacao.md). Os arquivos brutos do projeto não são modificados nem importados automaticamente na instalação.

- Aceita XLS e XLSX, duas planilhas correspondentes, até 10 MB cada e 50 mil linhas por planilha.
- Valida assinatura do arquivo e limita a expansão de XLSX e o tamanho total da requisição.
- Aceita formato tabular e o layout por blocos de produto do ERP.
- Exige fábrica explícita, identidade do pedido, documento, datas, valores e todos os itens.
- Utiliza valores decimais e preserva o subtotal oficial do ERP, com tolerância limitada ao arredondamento do preço exibido.
- Cargas inválidas não alteram os dados comerciais. O histórico registra erros de processamento.
- Reenvios idênticos não duplicam pedidos. Alterações exigem marcar a opção correspondente e não podem remover produtos existentes nem trocar cliente/fábrica.
- O SKU é preservado, inclusive sufixos de embalagem; conflitos de SKU entre fábricas são rejeitados.
- Cargas simultâneas em PostgreSQL são serializadas por bloqueio transacional.

## Atualização de uma instalação existente

Faça backup do banco e das chaves antes de atualizar. Em bases **já versionadas pelo Alembic**, confira `python -m alembic current` e execute `python -m alembic upgrade head`.

A cadeia agora inclui o schema inicial e implementa a migração histórica de grupo econômico. Uma base antiga criada manualmente com `create_all`, ou com colunas adicionadas fora do Alembic, precisa de conferência individual antes do alinhamento de versão. **Não execute `stamp head` indiscriminadamente:** isso pode esconder colunas ausentes. A instalação não altera automaticamente bases legadas não versionadas.

Novas escritas são cifradas; a leitura mantém compatibilidade com texto legado. A migração estrutural não reconstrói documentos que já foram anonimizados. Clientes sem `cnpj_hash` bloqueiam importações até reconciliação, para evitar duplicação. A precisão monetária existente é convertida para centavos; subtotais antigos são derivados da quantidade e do preço existentes.

## Verificações

```sh
python -m pytest tests -q
python -m alembic check
cd frontend
>>>>>>> Stashed changes
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

<<<<<<< Updated upstream
## Importar Excel

Envie os relatórios **de pedidos/cabeçalho** e **de produtos vendidos/itens**, do mesmo período. A interface aceita arquivos XLS e XLSX de até 10 MB cada. Os arquivos são enviados à base real do backend; confirme a escolha antes de importar.

O resultado reproduz a mensagem retornada pelo servidor. Contagens só aparecem quando o backend as fornece. O histórico persistente de cargas ainda depende de uma rota adicional. A documentação detalhada da interface está em [frontend/README.md](frontend/README.md).

## Estrutura

- `frontend/`: React, Vite, serviços de API e testes de contrato.
- `src/backend/`: código Python/FastAPI e serviços comerciais.
- `alembic/`: migrações do banco PostgreSQL.
- `scripts/`: utilitários locais do backend.
- `data/`: dados e documentação do tratamento de planilhas.
- `docs/`: requisitos e referências visuais.
- `tests/`: testes existentes do backend.

O contrato publicado em `/openapi.json` é a referência da integração. As rotas de analytics presentes no código local não estão registradas na API publicada. Alterar o backend local não altera o serviço no Render sem uma publicação correspondente.

## Cadastro e aprovação por e-mail

O backend requer Python 3.11 ou superior. A configuração e publicação da correção
de cadastro estão em [docs/autenticacao-email.md](docs/autenticacao-email.md).
Falhas de envio retornam 503 com orientação para retomar o cadastro, mantendo
o usuário bloqueado até a aprovação. O login continua disponível quando o
provedor de e-mail está indisponível.

Testes isolados (sem banco de produção nem envio real de e-mails):

```bash
python -m pytest tests/test_autenticacao_email.py tests/test_api.py tests/test_seguranca.py -q
```

## Colaboradores

- Ricardo Nilson Klug
- Rafael Júlio Klug
=======
Os testes de navegador iniciam uma API isolada com dados sintéticos e SQLite temporário, sem SMTP e sem acesso ao banco operacional. No Windows, defina `E2E_PYTHON` com o caminho absoluto de `.venv\Scripts\python.exe`; no macOS/Linux, o caminho padrão é `../.venv/bin/python`. Para usar o Chrome instalado, defina `PLAYWRIGHT_CHANNEL=chrome`.

A CI verifica backend, migrações em PostgreSQL, lint, build e fluxos em desktop/celular. `/` indica processo online; `/health/ready` verifica acesso à tabela de usuários. Há limitação de tentativas de autenticação por processo; instalações com múltiplas instâncias precisam de limitação compartilhada no proxy.

## Estrutura

- `frontend/src/paginas`: páginas e estilos.
- `frontend/src/componentes`: componentes compartilhados e estados de consulta.
- `src/backend/app/api`: contratos HTTP e autorização.
- `src/backend/app/services`: importação, autenticação e análises comerciais.
- `src/backend/app/models`: persistência SQLAlchemy.
- `alembic/versions`: evolução do banco.
- `tests`: testes do backend e servidor sintético para E2E.
- `frontend/tests`: testes de navegador.
>>>>>>> Stashed changes
