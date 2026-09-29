# Frontend — Rio Verde Representações

Interface React/Vite em português, com tema claro e logo original. Consome a API publicada em [Render](https://sistema-de-recomendao-comercial.onrender.com/docs). Não usa dados demonstrativos nem requer banco local.

## Executar

Na pasta `frontend`:

```bash
npm ci
npm run dev
```

Entre com uma conta **ativa e aprovada** do backend. Importar arquivos exige perfil `admin` ou `gestor`. Não existem credenciais fixas no frontend. A senha não é persistida; o token e os dados da sessão ficam no `sessionStorage` da aba. Uma resposta 401 encerra a sessão e retorna ao login.

Em desenvolvimento, o Vite encaminha `/api` para o Render. Na compilação de produção, a interface chama a URL do Render diretamente. Para outra instalação, defina `VITE_API_URL` com a URL completa até `/api/v1`, conforme `.env.example`, e reinicie/recompile. A API deve permitir a origem do frontend em sua configuração CORS.

## Funcionalidades conectadas

| Tela | Integração |
| --- | --- |
| Login | `POST /auth/login`, formulário OAuth2 com `username` e `password`. |
| Visão geral | `GET /clientes/alertas/home?limite=50`; cartões com filtros por busca, prioridade e tipo. As contagens representam somente os alertas recebidos. |
| Clientes | `GET /clientes/busca?termo=...`, a partir de dois caracteres, com ordenação dos resultados por nome ou cidade. A busca não equivale a uma listagem completa da carteira. |
| Cliente 360° | `GET /clientes/{id}`; comparação de faturamento, ciclos por fábrica, reposição, abandono e expansão de mix. |
| Produtos complementares | `POST /clientes/cross-selling?top_n=4`, com array direto dos IDs selecionados dentre os produtos do histórico disponíveis no dossiê. |
| Importação | `POST /cargas/excel`, multipart com `arquivo_cabecalho` e `arquivo_itens`. Após confirmação, invalida as consultas para buscar dados atualizados. |

Todas as rotas acima usam o prefixo `/api/v1`. Consultas protegidas enviam `Authorization: Bearer ...`. A busca cancela requisições antigas; erros e indisponibilidade do Render são apresentados com opção de tentar novamente.

## Planilhas

Selecione os dois relatórios do ERP para o mesmo período: **pedidos/cabeçalho** e **produtos vendidos/itens**. A interface aceita XLS/XLSX e limita cada arquivo a 10 MB. O tratamento e a persistência são de responsabilidade do backend publicado.

A resposta da importação tem formato livre: a interface apresenta a mensagem do servidor e só mostra contagens quando elas são fornecidas explicitamente. Não inventa quantidades nem histórico local. Em timeout, o servidor pode continuar processando; a interface orienta conferir os dados antes de reenviar e não repete o envio automaticamente.

## Limites do contrato publicado

A API atual não oferece faturamento consolidado, série mensal global, metas, filtros por representante/segmento/período, listagem paginada de todos os clientes, histórico de importações, recuperação de senha ou `/auth/me`. A interface não chama essas rotas nem apresenta dados fictícios para preencher as lacunas. Faturamento é exibido apenas quando retornado na ficha individual. Recomendações de whitespace regional continuam excluídas.

## Organização e verificação

- `src/servicos/api.js`: origem, token, tratamento de erros, timeout e cancelamento.
- `src/servicos/autenticacao.js` e `importacao.js`: contratos de escrita.
- `src/ganchos/useConsulta.js`: consultas canceláveis, sem reaproveitar respostas de buscas anteriores.
- `src/componentes/comercial/`: cartões, filtros, estados de consulta, perfil e recomendações reutilizáveis.
- `src/paginas/PainelComercial.jsx`: navegação e atualização após importar.

```bash
npm test
npm run lint
npm run build
```

Os testes automatizados verificam o contrato com respostas controladas; não enviam dados ao Render. Para validar com a base real, entre com uma conta autorizada, procure um cliente conhecido e envie um par de relatórios apropriado. Confira a mensagem da importação e consulte novamente o cliente.
