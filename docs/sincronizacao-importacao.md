# Reimportação e sincronização mensal

Existem dois modos na tela de importação:

- Atualizar pedidos informados: adequado a arquivos parciais. Atualiza cabeçalhos e substitui os itens dos pedidos com detalhamento na carga. Quantidades menores e preços alterados substituem os anteriores. Pedidos ausentes não são excluídos; pedidos que vierem sem itens conservam os itens conhecidos.
- Sincronizar mês completo: exige o mês explícito e arquivos com todas as vendas desse mês, de todos os vendedores e fábricas. Remove pedidos daquele mês que não constam nos cabeçalhos e substitui os itens dos pedidos informados, inclusive quando a lista ficou vazia. Não remove cadastros de clientes, produtos ou fábricas.

O mês é determinado pela data de emissão do pedido. Não se deve escolher a sincronização para relatórios filtrados por vendedor, fábrica ou cliente. O sistema não consegue comprovar, apenas pelos registros, que o arquivo está completo: essa confirmação é responsabilidade de quem importa.

A conferência é somente leitura. Mostra o número de pedidos a excluir, linhas de itens a remover, produtos por pedido com quantidade reduzida e uma amostra de até 100 pedidos excluídos. A quantidade de linhas removidas inclui os itens dos pedidos excluídos. Linhas de itens substituídas por outra quantidade do mesmo código são contadas como reduções, não como remoções de produto.

Na confirmação, arquivos, modo, mês e estado dos pedidos são verificados novamente. Alterações posteriores à conferência exigem nova conferência. As exclusões, atualizações e o registro da importação fazem parte da mesma transação; uma falha desfaz a operação inteira. No PostgreSQL, uma trava impede duas importações simultâneas.

O histórico registra modo, mês e contagens. O campo interno `importacoes.resumo_json` também conserva os pedidos excluídos e seus itens para rastreabilidade. Não existe uma função de restauração na interface.

Um mês sem vendas pode ser sincronizado com arquivos que contenham os cabeçalhos esperados e nenhuma linha de dados. A conferência mostrará todos os pedidos daquele mês como exclusões. Arquivos sem estrutura válida são rejeitados. Datas fora do mês, datas futuras e itens sem cabeçalho correspondente bloqueiam a sincronização antes de gravar.

Pedidos diretos de fábrica continuam permitidos sem itens. No modo mensal, a ausência de detalhamento limpa itens antigos daquele pedido e as análises passam a tratá-lo como pedido sem itens conhecidos.

Para disponibilizar a funcionalidade em um ambiente existente, executar `alembic upgrade head` antes de iniciar a API. A revisão `20261028_sincronizacao` acrescenta somente o campo de auditoria; não exclui pedidos. O `start.py` já executa as migrações ao iniciar no Render. Nenhuma sincronização é executada automaticamente durante a implantação.
