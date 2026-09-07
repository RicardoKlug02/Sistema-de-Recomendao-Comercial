# Frontend — Sistema de Recomendação Comercial

Aplicação React com Vite, baseada em `docs/Tela de login.png` e `docs/wireframe_dashboard.png`. Não utiliza bibliotecas adicionais de gráficos ou componentes.

## Executar

Na pasta `frontend`, execute `npm install` e `npm run dev`.
`npm run build` gera a versão de produção

## Fluxo disponível

- O painel apresenta quatro indicadores, faturamento mensal, vendas por categoria, cinco principais clientes, últimas importações e oportunidades recentes.
- O menu navega pelos resumos do próprio painel. Clientes e Importação ainda não são páginas de cadastro ou envio de arquivos.
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

Nomes próprios da aplicação estão em português. Propriedades nativas de HTML e React, como `children`, `className` e `onClick`, mantêm os nomes exigidos pelas bibliotecas.

## Integração futura

Substitua as simulações em `entrar({ email, senha })` e `solicitarRecuperacaoSenha({ email })` quando houver contrato de autenticação. O login retorna `{ usuario: { email } }`; falhas devem rejeitar a promessa. Os dados demonstrativos estão separados para futura integração com os endpoints comerciais. O servidor deverá autenticar e autorizar o acesso aos dados reais.

## Conferência manual

1. Enviar campos vazios e e-mail inválido; conferir mensagens e foco no primeiro campo inválido.
2. Entrar com dados válidos e verificar todos os blocos do dashboard.
3. Navegar pelo menu; verificar rolagem, foco e indicação da seção escolhida.
4. Abrir uma oportunidade; fechar com Escape e com o botão, verificando retorno do foco.
5. Conferir layout no celular, rolagem interna da tabela e navegação pelo teclado.
6. Sair, testar recuperação e recarregar a página para conferir a sessão em memória.
