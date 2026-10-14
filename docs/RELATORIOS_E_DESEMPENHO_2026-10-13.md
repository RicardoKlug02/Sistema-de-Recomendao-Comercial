# Relatórios, filtros e desempenho - 13/10/2026

## Operação

A seção Relatórios permite escolher uma rede de clientes e uma fábrica, ou Todas as fábricas. O PDF e a prévia mostram os códigos comprados por todos os CNPJs da rede, com descrição, fábrica, data do último pedido com aquele produto, último preço unitário, número do pedido e cliente que realizou essa compra. Códigos iguais de fábricas diferentes permanecem em linhas distintas. A data e o preço vêm do mesmo registro; em pedidos no mesmo dia, o registro mais recente desempata. Pedidos sem itens são informados como limitação e não geram códigos ou preços inventados. O relatório é protegido pela mesma autenticação das vendas.

Os filtros por fábrica estão disponíveis na visão geral, lista e ficha de clientes, relatórios e central de alertas. Filtrar a ficha limita o faturamento, pedidos, comparações e produtos à fábrica escolhida. A inatividade geral do cliente continua considerando todas as suas compras: selecionar uma fábrica não torna inativo um cliente ativo em outra.

A central pagina clientes, com um card por cliente. Todos os sinais ficam dentro desse card, acessíveis em Ver fábricas e produtos. Os filtros de tipo, fábrica e vendedor são aplicados antes do agrupamento, e a tela informa separadamente o número de clientes e de alertas. A regra de 90 dias permanece.

Os códigos agora aparecem nos rankings de produtos, reposição, abandono, sugestões de mix e alertas de produtos. A tipografia usa fontes de interface modernas disponíveis no dispositivo, sem baixar fontes de terceiros.

## Desempenho

- Consumo para recomendações somado no PostgreSQL por cliente/produto, evitando transferir todas as linhas de itens.
- Consultas de produtos e fábricas das recomendações reunidas em uma consulta, retirando buscas uma a uma no Cliente 360º.
- Painel e alertas carregam colunas necessárias; nomes de clientes no painel são decifrados somente para o conjunto consultado.
- Busca por documento utiliza diretamente o índice protegido de CNPJ/CPF; buscas por nome continuam preservando a criptografia e precisam percorrer os nomes elegíveis.
- Troca de filtros cancela solicitações antigas da interface. A lista de fábricas é compartilhada pelas telas.
- Última compra por produto calculada no banco com função de janela, sem carregar todos os itens da rede para decidir em Python.

Teste controlado no PostgreSQL/Neon, em esquema temporário com 20.000 itens fictícios: consulta anterior 0,573 s; consumo agregado 0,054 s; relatório de uma rede com 20 códigos 0,278 s. São medidas pontuais desse cenário, não garantia de tempo de resposta da aplicação inteira. Toda a transação foi desfeita e os dados reais foram preservados.

## Verificação

48 testes de backend passaram, incluindo rede com múltiplos CNPJs, códigos iguais entre fábricas, origem do último preço, filtros de clientes e faturamento, agrupamento de quatro sinais em um card e autenticação do PDF. Lint e compilação do frontend passaram. A demonstração local confirmou a prévia e o download autenticado; o arquivo baixado continha código, preço e cadastro fiscal corretos. O PDF de exemplo com dados fictícios foi renderizado e inspecionado nas três páginas, com cabeçalho repetido, rodapé e códigos longos sem corte.

A suíte Playwright do projeto recebeu cobertura para a nova tela e os mocks de fábricas; sua execução automatizada local não foi realizada porque a dependência @playwright/test não está instalada neste checkout. A verificação visual e do download foi feita no navegador conectado.

Não há migrações novas nem reset do banco. A nova dependência do backend é ReportLab. A publicação precisa compilar o frontend e reinstalar requirements.txt, como já faz o build do Render.

## Análise de implantação e novos relatórios

A tela Análise do sistema usa 29/09/2026 como início ajustável e compara a mesma carteira comercial conhecida até a véspera da implantação. Clientes e relações cliente × fábrica ficam inativos após 90 dias. Produtos em abandono seguem a regra existente: pelo menos três datas distintas de compra, 60 dias sem comprar e mais de 2,5 vezes o ciclo médio inteiro. Pedidos posteriores sem itens deixam o abandono sem confirmação. A base de produtos e clientes permanece fixa para não confundir aumento de cadastros com piora. Reativações são comparadas em períodos de igual duração. Novos clientes são apresentados separadamente.

Cada rede econômica representa um cliente comercial. Todos os CNPJs da rede compõem compras, primeira compra, atividade, reativações e ciclo de produto. Cadastros sem rede permanecem individuais. O painel, os rankings e a central de alertas agrupam por essa identidade. Cliente 360º abre consolidado e permite consultar cada cadastro fiscal. A busca aceita dados de qualquer cadastro da rede. Semelhança de razão social ou raiz de CNPJ não cria agrupamento: é preciso informar corretamente a rede nas planilhas.

Foram adicionados cinco relatórios paginados, com filtros e exportação autenticada em PDF: mapa cliente × fábrica (inclui sem compra), resultado das reativações (pedido de retorno e continuidade sem duplicar episódios), clientes inativos na data escolhida, evolução do preço por código e fábrica (compra anterior inclusive fora do período, somando os CNPJs da rede), e regiões imediatas com variação de venda e quantidade de clientes em relação à média das regiões conhecidas do vendedor. Redes em regiões diferentes contam uma vez por região; totais regionais de clientes não são aditivos. O mapa e a lista de inativos são posições na data final; o início do período não restringe seu histórico. PDF com mais de 5.000 linhas exige refinar os filtros; a consulta em tela continua completa e paginada.

O comparativo é observacional, sem comprovar que a mudança foi causada pelo sistema. Ainda não há vínculo entre contato/ação do vendedor e pedido. A interpretação depende da cobertura do histórico importado. Quedas e variações são informativas, sem novos alertas automáticos. Datas de referência da API usam o fuso de São Paulo.

Validação adicional: 60 testes passaram, incluindo compra em CNPJ diferente sem falso novo cliente, continuidade de preços entre CNPJs, datas de compra duplicadas na rede, abandono sem confirmação, ficha fiscal e consolidada, carteira fixa, filtros e PDF. Lint e build do frontend passaram. Não é necessário reset ou migração do Neon.
