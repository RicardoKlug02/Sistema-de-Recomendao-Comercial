# Revisão dos pedidos e da integridade das análises

## Decisões de negócio confirmadas

- Bonificações e duplicidades não integram as análises comerciais.
- O pedido 31781 é um ajuste comissionado: seu valor integra o faturamento, mas não representa nova compra, não reinicia inatividade e não altera o ciclo dos produtos.
- Os pedidos 37066 e 37182 são bonificações.
- Gravatal integra a rede GB2. O vínculo atual da rede consolida também as compras históricas dos seus CNPJs.
- Um pedido sem itens exige conferência. A ausência dos itens não comprova uma venda direta de fábrica.

## Procedimento para validar a base existente

1. Obter no Mercos os cabeçalhos e itens completos de cada mês, de toda a equipe. Manter os arquivos originais para conferência e incluir o tipo do pedido nos cabeçalhos.
2. Conferir a prévia antes de confirmar a importação: tipos desconsiderados, pedidos sem itens e mudanças de rede. A sincronização mensal considera ausências como exclusões; usar somente arquivos completos e o período correto.
3. Na seção de revisão de pedidos da importação, começar pelos pedidos sem itens e pendentes. Consultar o pedido no sistema de origem e registrar classificação, motivo e referência da conferência. É possível buscar um número e consultar todas as classificações.
4. Classificar como venda direta somente após confirmação documental ou com o responsável. Uma venda direta confirma a compra na fábrica, mas não os códigos adquiridos.
5. Conferir amostras por rede e fábrica, comparando faturamento, última compra e origem dos avisos com o Mercos. Comparar também os totais mensais, considerando separadamente ajustes comissionados.

Cada decisão preserva o pedido e gera histórico de auditoria. Reimportações preservam as classificações manuais. Alterações simultâneas são detectadas antes de salvar.

## Limites da validação

Os tipos originais de todos os pedidos antigos não foram armazenados pela versão anterior. Não é possível certificar a base inteira somente com os registros atuais; é necessário confrontá-los com a origem. A listagem de revisão identifica pedidos sem itens e permite revisão individual; não constitui um detector automático geral de duplicidades ou divergências financeiras.

## Correções e verificações

- Evidências por pedido, data, CNPJ e código original nas análises de produtos, alertas e histórico incompleto.
- Consolidação por rede e correção da atribuição de vendedor e da origem fiscal nos relatórios de inatividade.
- Separação entre valor comissionado e nova compra nas consultas comerciais.
- Validação do tipo de pedido e das mudanças de rede na importação.
- Testes: 113 testes de backend, 32 testes unitários de frontend e 30 testes de interface; lint, build e verificação das migrações PostgreSQL concluídos.

Em 09/11/2026, a migração foi aplicada ao Neon e os três pedidos acima foram classificados, com auditoria. A verificação com o código novo confirmou ausência das falsas pendências de produtos da Orion e da falsa inatividade da GB2 na Cibra. A versão do aplicativo precisa ser publicada para que o Render aplique a nova classificação nas consultas.
