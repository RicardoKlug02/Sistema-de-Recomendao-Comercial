# Frontend — Sistema de Recomendação Comercial

Aplicação React com Vite, baseada em `docs/Tela de login.png` e `docs/wireframe_dashboard.png`. Não utiliza bibliotecas adicionais de gráficos ou componentes.

## Executar

Na pasta `frontend`, execute `npm install` e `npm run dev`.
`npm run build` gera a versão de produção

## Fluxo disponível

- O painel apresenta quatro indicadores, faturamento mensal, vendas por categoria, cinco principais clientes, últimas importações e oportunidades recentes.
- O menu abre a tela de Importação; Clientes continua navegando ao resumo do painel.
- “Ver detalhes” abre os dados da oportunidade em um diálogo, fechado pelo botão ou pela tecla Escape, com retorno do foco ao botão de origem.
- As colunas do gráfico mostram os valores ao receber foco ou passar o mouse.
- “Sair da conta” retorna ao login. A sessão fica apenas em memória; recarregar exige novo acesso. Senhas e tokens não são persistidos.
- A recuperação de senha é simulada
- Os dados do painel são demonstrativos

## Responsabilidades

| Arquivo em `src/` | Responsabilidade |
| --- | --- |
| `Aplicacao.jsx` | Alternar login, recuperação e painel; manter a sessão em memória. |
| `componentes/CartaoAutenticacao.jsx` | Estruturar o título e conteúdo da autenticação. |
| `componentes/CampoFormulario.jsx` | Exibir campo, rótulo e erro acessível. |
| `componentes/FormularioAutenticacao.jsx` | Validar e enviar login ou recuperação, com feedback e controle de envio. |
| `componentes/MenuLateral.jsx` | Exibir navegação, usuário e saída. |
| `componentes/Cartao.jsx` | Compartilhar estrutura visual e título acessível entre os blocos do painel. |
| `componentes/CartaoIndicador.jsx` | Exibir valor e contexto de um indicador. |
| `paginas/PainelComercial.jsx` | Compor o dashboard e controlar navegação e detalhes. |
| `servicos/autenticacao.js` | Validar e-mail e simular login e recuperação. |
| `servicos/dadosPainel.js` | Centralizar dados demonstrativos e formatação monetária. |
