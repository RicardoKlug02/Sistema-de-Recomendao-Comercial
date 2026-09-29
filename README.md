# Sistema de Recomendação Comercial — Rio Verde

Sistema de suporte à decisão para representantes comerciais, com acompanhamento de clientes, alertas de recompra e recomendações baseadas no histórico da carteira.

## Estado atual

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
cd frontend
npm ci
npm run dev
```

Abra o endereço informado pelo Vite, normalmente `http://localhost:5173`. Entre com uma conta ativa e aprovada da API. Não é necessário iniciar Python ou PostgreSQL para usar o backend do Render.

Em desenvolvimento, as chamadas passam pelo proxy do Vite para o Render. Na produção, a interface usa diretamente a API hospedada. Para substituir a URL, consulte `frontend/.env.example` e reinicie/recompile a interface. Tokens e senhas não devem ser colocados nessas variáveis.

Verificações na pasta `frontend`:

```bash
npm test
npm run lint
npm run build
```

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
