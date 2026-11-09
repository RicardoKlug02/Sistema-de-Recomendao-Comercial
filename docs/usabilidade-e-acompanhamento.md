# Usabilidade e acompanhamento comercial

## Leitura e navegação

- Os produtos exibem fábrica, código e descrição no Cliente 360, no ranking do painel e na comparação de quantidades. A API da ficha preserva a identificação da fábrica em recomendações, reposição, abandono e recompra não confirmada.
- O Cliente 360 separa a atividade da fábrica (90 dias) do atraso no ciclo habitual. Uma compra isolada não é apresentada como um ciclo já estimado.
- Textos de leitura e tabelas usam tamanho maior, números financeiros alinhados, botões com área de interação ampliada e foco visível. Explicações de ciclo e recomendação ficam em detalhes expansíveis.
- Filtros de visão geral, clientes, alertas, análises e relatórios são preservados enquanto a sessão da interface estiver aberta. A memória não passa para outro usuário e não persiste após recarregar a aplicação.
- Ao abrir um cliente pelos alertas ou painel, o filtro de fábrica acompanha a navegação. O botão de retorno restaura a seção de origem, seus filtros e a posição de rolagem. Busca e página da lista de clientes são preservadas.
- Consultas com erro oferecem nova tentativa sem recarregar a aplicação. O refresh da mesma consulta mantém o conteúdo anterior durante a atualização; mudanças de filtros não exibem os dados do filtro anterior.

## Filtros das listas de produtos

As listas de reposição, abandono confirmado, recompra não confirmada e ampliação de mix compartilham busca por código, nome ou fábrica. A busca combina palavras de campos diferentes e ignora acentos e maiúsculas. Quando há mais de uma fábrica na lista, um seletor permite restringir os produtos. Listas longas começam com cinco produtos; Mostrar mais acrescenta até dez e Mostrar menos retorna aos cinco iniciais.

A comparação de quantidades com a média histórica começa com dez produtos, acrescentando dez por clique. Seus filtros combinam busca, fábrica e variação: queda, aumento, estabilidade ou comparação indisponível. Produtos sem base, com histórico insuficiente ou com itens incompletos ficam no último grupo, sem serem interpretados como queda ou variação zero.

Os controles mostram quantos produtos estão visíveis, quantos correspondem aos filtros e o total da lista. Limpar filtros restaura a busca, os seletores e o limite inicial. Cada lista mantém controles independentes; alterar uma delas não filtra as outras nem modifica os indicadores financeiros ou os alertas. A paginação é visual e trabalha sobre os produtos já recebidos pela ficha.

O relatório de códigos comprados pela rede usa os mesmos controles, começando com vinte produtos e acrescentando vinte por clique. A busca e o filtro local não limitam o PDF: a exportação continua considerando a rede e o filtro de fábrica do cabeçalho, conforme indicado na tela.

## Histórico disponível

A visão geral exibe primeira/última venda conhecida, quantidade de pedidos e última importação registrada. Vendas futuras são excluídas desse resumo. A faixa não comprova que todos os meses foram importados. A nota de primeira compra registrada na base permanece. Datas e horários são apresentados em português brasileiro, com horários em America/Sao_Paulo.

## Acompanhamento dos alertas

Cada cliente comercial tem acompanhamento compartilhado com a equipe, nas situações Pendente, Contatado, Aguardando retorno e Dispensado. Todos os usuários aprovados que podem consultar a carteira podem registrar ações. Cada gravação cria um evento com usuário, horário, observação e próxima data; eventos anteriores são preservados.

- Dispensar exige motivo.
- Aguardar retorno exige próxima data, hoje ou futura.
- Contatado admite próxima data opcional. Datas vencidas são sinalizadas ao consultar.
- Pendente e Dispensado não admitem data futura de contato no mesmo registro.
- Alterações concorrentes são recusadas com pedido para atualizar a lista; os usuários não sobrescrevem silenciosamente o acompanhamento de outro.
- Uma assinatura dos sinais completos do cliente (incluindo referência da compra e prioridade) detecta mudanças, independentemente dos filtros usados na tela. Novos sinais ou agravamentos recolocam o acompanhamento em Pendente, preservando os eventos anteriores.
- O acompanhamento não remove os alertas analíticos nem altera contagens de inatividade, vendas ou recomendações. Para reduzir a lista, usar o filtro de acompanhamento.
- Ao consultar, são mostrados até 30 eventos mais recentes; todos permanecem no banco. A funcionalidade não envia lembretes ou mensagens automaticamente.

## Banco e verificações

A migração `20261018_acoes`, posterior a `20261018_historico`, cria `acoes_alerta`. A inicialização do servidor aplica as migrações antes de atender requisições. A verificação em PostgreSQL usa esquema temporário descartado por rollback, sem migrar as tabelas públicas.

Os testes cobrem contrato da ficha com fábrica, ciclo atrasado com fábrica ativa, resumo do histórico, autenticação, validação das ações, compartilhamento por rede, concorrência e reabertura por mudança de sinais. A verificação de navegador usa dados artificiais e intercepta todas as chamadas de API; não grava na produção.
