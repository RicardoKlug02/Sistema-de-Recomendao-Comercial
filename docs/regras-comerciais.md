# Regras comerciais confirmadas em 18/10/2026

## Redes e vendedores

- A rede é o cliente comercial; os CNPJs preservam o detalhe fiscal.
- A identificação da rede ignora maiúsculas/minúsculas e espaços extras, inclusive entre palavras. A grafia armazenada é preservada para exibição. Nomes diferentes não são unidos por aproximação.
- A exceção de vendedor considera o vendedor do último pedido do cliente comercial, independentemente da fábrica, até a data analisada. No mesmo dia, o maior ID do pedido resolve o desempate.
- Essa referência também vale ao consultar o detalhe de um CNPJ. A abrangência territorial continua sendo avaliada pelos estados dos cadastros fiscais.
- Uma rede com filiais em estados diferentes continua elegível quando existir uma filial permitida. A exceção cadastrada para um vendedor permite atender também os estados abrangidos pela restrição correspondente. Outras restrições independentes continuam valendo.
- O vendedor histórico de cada venda não é alterado. Os filtros financeiros continuam mostrando quem realizou cada pedido; o vendedor de referência serve às exceções e à atribuição das ações atuais.

## Datas e evidência incompleta

- Importações com emissão futura são rejeitadas na conferência e novamente antes da gravação. A mensagem identifica pedido, fábrica e linha para correção; nenhuma venda da carga é salva.
- Os cálculos de recomendação excluem pedidos posteriores à data analisada. A data corrente segue America/Sao_Paulo.
- Pedidos válidos sem itens entram em vendas e atividade da fábrica. Não confirmam quais códigos foram comprados.
- Quando existe pedido sem itens posterior à última compra conhecida de um produto naquela fábrica/rede, o produto recebe a indicação de recompra não confirmada no Cliente 360. Não é contado como abandono confirmado nem gera recomendação de reposição ou alerta de risco de produto baseado nessa ausência.
- Compra conhecida posterior do produto elimina a incerteza desse código. Pedidos de outra fábrica não criam incerteza para ele.
- A regra de 90 dias para inatividade de cliente/fábrica permanece. A regra de abandono por ciclo também permanece, ressalvada a evidência incompleta.

## Vigência e substituições

- Restrições são avaliadas no período entre início e fim, inclusive. Uma restrição iniciada em julho não bloqueia uma análise de junho.
- A substituição oferece a opção `unificar_historico`. Ligada, após o início da regra, unifica também compras anteriores; desligada, unifica apenas movimentações a partir do início. Antes da vigência, análises preservam os códigos originais em ambos os casos.
- Mesmo sem unificar as compras anteriores, sugestões de novos produtos usam o sucessor e não oferecem novamente o equivalente já comprado.
- Pedidos, preços e códigos fiscais não são reescritos. A migração `20261018_historico` acrescenta a opção com padrão ligado para preservar o comportamento das regras existentes.
- Para encerrar uma regra preservando sua aplicação nas datas anteriores, informar o fim da vigência. Desativação continua sendo anulação da regra, incluindo sua aplicação em análises anteriores, conforme o aviso da tela. Não equivale a um histórico imutável de versões de regras.

## Validação e publicação

Os testes usam dados artificiais, incluindo referências a Depecil, Cibra e códigos 21001/21053. Nenhuma dessas regras foi cadastrada em produção automaticamente. O exemplo de Cibra em julho foi usado com início em 01/07/2026 apenas no cenário isolado.

A suíte cobre identificação de redes, corte temporal, bloqueio de importação futura, incerteza por pedido sem itens, vendedor global e exceções no detalhe fiscal, limites de vigência, substituição com/sem histórico anterior, persistência da opção pela API e preservação dos valores originais.

Antes de publicar, executar testes, build do frontend e verificar migrações. O inicializador `start.py` aplica `alembic upgrade head` antes de iniciar a API. A validação com `scripts/verificar_migracoes.py` usa um esquema temporário no PostgreSQL e rollback, sem atualizar a revisão das tabelas públicas.

Primeira compra: manter sempre o aviso de "primeira compra registrada na base", tanto para o escritório quanto para cada fábrica, mesmo após importar os históricos de 2025 e eventualmente 2024. A indicação considera o histórico disponível; importações anteriores podem mudar datas, classificações e a composição da carteira inicial. O mesmo cuidado vale ao sugerir contato para um segundo pedido.
