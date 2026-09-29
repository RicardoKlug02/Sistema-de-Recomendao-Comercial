# Contrato de importação

A importação combina um arquivo de pedidos e um de itens. Ambos devem representar o mesmo conjunto completo de pedidos. É feita uma validação de todo o lote antes da gravação; conflitos encontrados durante a persistência também causam rollback de toda a carga.

## Formato tabular

### Pedidos

| Coluna | Regra |
| --- | --- |
| pedido | Identificador textual de até 50 caracteres, único no arquivo e global na base |
| cnpj_cpf | Documento com 11 ou 14 dígitos; preservar zeros à esquerda |
| cliente | Nome do cliente, obrigatório |
| fabrica | Nome da fábrica/representada, obrigatório |
| data | Data Excel, DD/MM/AAAA ou AAAA-MM-DD, não futura |
| valor_total | Positivo, até duas casas decimais; valores brasileiros são aceitos |
| vendedor, rede, cidade, estado, micro_regiao | Opcionais; ausência não apaga metadados existentes |

### Itens

| Coluna | Regra |
| --- | --- |
| pedido | Deve existir no arquivo de cabeçalho |
| sku | Código literal, até 150 caracteres; sufixos são preservados |
| nome_produto | Nome obrigatório, até 255 caracteres |
| quantidade | Inteiro positivo; frações são rejeitadas, nunca truncadas |
| preco_unitario | Positivo, até duas casas decimais |
| subtotal | Opcional; quando ausente, quantidade × preço. Quando informado, é preservado |
| categoria | Opcional; permite segmentação nos relatórios |

Cada pedido deve possuir itens. Itens exatamente repetidos são rejeitados para evitar duplicação acidental. Um SKU não pode ser vinculado a fábricas diferentes nesta versão. O sistema não transforma automaticamente códigos terminados em U/u.

O subtotal pode divergir de quantidade × preço somente até `quantidade × 0,005 + 0,005`, cobrindo o arredondamento do preço unitário exibido pelo ERP. O subtotal continua exigindo duas casas decimais. A soma dos subtotais deve coincidir com o total do pedido, com tolerância máxima de R$ 0,01. Descontos, fretes e outros ajustes não representados precisam ser conciliados na origem; o sistema não inventa compensações.

## Relatórios legados do ERP

O leitor encontra o cabeçalho nas primeiras 30 linhas e reconhece, entre outros, os nomes `Data de emissão`, `Representada`, `Razão Social`, `CNPJ/CPF`, `Rede de clientes`, `Vendedor(a)` e `Total em produtos`.

No arquivo de produtos, reconhece seções `Produto: SKU - Nome` e linhas com data, pedido, cliente, criador, preço, quantidade e subtotal. Rodapés conhecidos de contagem/total são ignorados. Produto sem SKU, data inválida e linhas de conteúdo não reconhecido geram erro, com indicação da linha.

## Reenvio e atualização

- Reenvio idêntico: pedido contado como inalterado.
- Pedido alterado: exige consentimento na opção “Permitir atualizar pedidos existentes”.
- Nunca permite trocar a identidade cliente/fábrica de um pedido.
- Não permite remover produtos de um pedido por meio de planilha parcial.
- Correções que envolvam remoção de itens, pedidos cancelados, devoluções, SKUs compartilhados entre fábricas ou unidades fracionárias exigem um fluxo específico ainda não implementado.

O histórico guarda arquivos, responsável, data e mensagem do processamento. Erros de extensão, arquivo vazio ou tamanho são rejeitados antes do processamento e não geram uma carga persistida. O histórico de falhas de dados informa o primeiro problema encontrado para correção e reenvio.

## Conferência dos arquivos do repositório

A revisão dos arquivos brutos foi apenas de leitura. Foram identificadas divergências que impedem a importação estrita de alguns conjuntos: itens sem pedido correspondente, produto sem SKU e diferenças entre soma de itens e total do cabeçalho. Os arquivos não foram corrigidos automaticamente. Reexporte o mesmo conjunto de pedidos em ambos os relatórios e confira o relatório de erro antes de tentar novamente.
