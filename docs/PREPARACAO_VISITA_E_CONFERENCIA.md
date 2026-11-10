# Preparação da visita e conferência das cargas

## Uso

Na ficha do cliente, escolher rede/CNPJ e fábrica e abrir **Preparar visita e exportar PDF**. Selecionar abandono, recompra ou ambos e os produtos desejados. A busca e o botão de mostrar mais limitam apenas a lista exibida. A quantidade selecionada informa o conteúdo completo do PDF. Preços ficam ocultos inicialmente.

O relatório inclui códigos atuais e originais, descrição, fábrica, última compra conhecida, quantidade, ciclo, motivo da indicação, pedido e CNPJ de origem, data da análise e intervalo dos dados disponíveis no escopo. Preços opcionais representam a média ponderada das linhas equivalentes no último pedido conhecido; não representam uma cotação. Preço ausente aparece sem valor, não como zero. Produtos com recompra não confirmada não integram as listas.

Na importação, a conferência após a gravação informa a posição da base no intervalo da carga: compras, itens, valor comissionado, ajustes sem nova compra, exclusões analíticas e compras sem itens pendentes de revisão. A posição fica salva no histórico de importações. Para sincronizações mensais, utiliza todo o mês. Para atualizações, utiliza o intervalo dos cabeçalhos válidos. Não se presume igualdade automática entre arquivo e base, nem se certifica completude da exportação. Importações antigas não possuem esse retrato.

Na central de alertas, o acompanhamento admite **Recompra realizada (informada)** e **Produto descontinuado (informado)**, com referência obrigatória na observação. O histórico preserva autor e data. São declarações da equipe, sem efeito em vendas, recomendações ou inatividade. Não substituem regras de substituição/restrição. Mudanças nos sinais continuam reabrindo o acompanhamento para revisão.

## Publicação

A migração `20261109_resultados_acoes` amplia as situações aceitas no banco. Deve acompanhar a publicação da API e do frontend. O processo de inicialização existente aplica as migrações. A conferência utiliza o JSON de auditoria de importações já existente. A base não é preenchida automaticamente.

## Verificação

Cobertura de rede/CNPJ, fábrica, seleção, autenticação, casos vazios, origem e preço no relatório; conferência persistida no histórico, separação de ajustes e bonificações, resultados com motivo obrigatório e manutenção dos sinais. PDFs de demonstração usam dados fictícios. Migração verificada em esquema PostgreSQL temporário com rollback.
