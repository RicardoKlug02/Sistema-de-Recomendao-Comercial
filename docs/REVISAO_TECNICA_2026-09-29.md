# Revisão técnica — Sistema de Recomendação Comercial

Data: 29/09/2026. Escopo: todos os arquivos de código da API, serviços, modelos, schemas, frontend, scripts, migrações e testes, além da configuração de execução e CI. Os oito pares de planilhas foram lidos apenas para conferir o comportamento do importador; nenhum dado foi gravado no PostgreSQL.

O projeto possui uma estrutura útil em FastAPI, SQLAlchemy e React, com autenticação JWT, aprovação de usuários, recomendações colaborativas, associação de produtos e análise de recompra. Entretanto, o backend está bloqueado na inicialização, há falhas que alteram ou eliminam informações na importação, e a interface continua demonstrativa. Os indicadores e alertas ainda não podem ser usados para decisões comerciais com confiança.

As prioridades abaixo significam: **P1**, corrigir antes de utilizar dados reais ou liberar a aplicação; **P2**, corrigir antes de considerar a funcionalidade concluída. Os trechos citados são do código existente, que não foi modificado durante a revisão.

## Achados prioritários

### 1. [P1] A API e os testes não conseguem carregar o módulo do banco

**Local:** `src/backend/app/core/database.py:29–33`.

O módulo calcula `DATABASE_URL`, mas chama `create_engine(settings.DATABASE_URL)` sem importar nem definir `settings`. A falha ocorre na importação, antes de qualquer requisição ou conexão com o banco. O comando original de testes parou com `NameError: name 'settings' is not defined` em `database.py:30`.

**Correção:** escolher uma única fonte de configuração e utilizá-la consistentemente. Se for `settings`, importá-la e incorporar nela a composição/normalização da URL; se for a variável local, utilizar a URL já calculada. Manter dois mecanismos independentes deixa o comportamento sujeito a divergências.

### 2. [P1] Os campos criptografados chamam funções inexistentes

**Local:** `src/backend/app/core/types.py:22–31`; `tests/test_seguranca.py:3–13`.

`EncryptedString` importa `encriptar_dado` e `decriptar_dado`, mas executa `encrypt_data` e `decrypt_data`. As duas chamadas produziram `NameError` no diagnóstico. Após resolver a inicialização do banco, a gravação ou leitura de clientes falhará nesses campos. Os testes também importam os nomes inexistentes.

**Correção:** uniformizar os nomes nos tipos, nos serviços e nos testes. Verificar uma gravação e leitura completas de cliente, além da criptografia isolada.

### 3. [P1] O ponto de entrada de produção aponta para um módulo que não existe

**Local:** `start.py:29`.

O launcher utiliza `src.backend.app.main:app`, enquanto a aplicação está em `src/backend/main.py`. Executar esse launcher não inicia a API.

**Correção:** usar `src.backend.main:app` e conferir o comando efetivamente utilizado no ambiente de execução.

### 4. [P1] Qualquer erro de migração pode ser ocultado por `stamp head`

**Local:** `start.py:12–20`.

Quando `alembic upgrade head` falha, o script tenta `alembic stamp head` sem identificar a causa. Isso pode marcar o banco como atualizado mesmo que as alterações não tenham sido aplicadas. O launcher continua depois da falha, inclusive quando a sincronização também falha.

**Correção:** interromper a inicialização em caso de falha de migração. Utilizar `stamp` somente em um procedimento explícito de reconciliação, após verificar o esquema existente.

### 5. [P1] O histórico de migrações não cria o esquema inicial

**Local:** `alembic/versions/fcd9d0c43f09_aumenta_tamanho_cnpj_cpf.py:15–27`; `alembic/versions/2bc7e3333923_adiciona_grupo_economico_cliente.py:21–24`; `scripts/init_db.py:18`.

A primeira revisão já altera a tabela `clientes`, presumindo sua existência. Não há uma revisão inicial criando as tabelas comerciais. A revisão que deveria adicionar `grupo_economico` contém apenas `pass`. Um PostgreSQL vazio não pode ser construído exclusivamente com o histórico versionado. Executar `create_all` com os modelos atuais também não constitui uma reprodução das revisões antigas: cria um esquema já avançado e não registra a versão do Alembic.

**Correção:** estabelecer uma base de migrações reproduzível, com tratamento separado para bancos existentes. Validar `upgrade head` em um PostgreSQL vazio e em uma cópia de um banco na versão anterior.

### 6. [P1] A migração para campos criptografados não converte os dados existentes

**Local:** `alembic/versions/c63ed4dbc762_add_blind_index_and_encrypted_columns.py:23–39`; `src/backend/app/core/security.py:43–49`; `src/backend/app/services/excel_service.py:181–214`.

A migração aumenta colunas e cria `cnpj_hash`, mas não cifra os valores antigos nem preenche o índice de busca. Se o banco já contém texto em claro, o novo tipo tentará decifrá-lo e retornará `[DADO CORROMPIDO]`. Clientes antigos com hash nulo também ficam fora do cache de importação; reimportar o mesmo documento pode criar outro cliente e dividir seu histórico.

**Correção:** planejar uma migração dos dados, com preenchimento dos hashes, conversão dos campos e reconciliação dos clientes existentes. Definir explicitamente como tratar documentos que já foram pseudonimizados e não permitem recuperar o original.

### 7. [P1] Todas as fábricas são substituídas pela primeira fábrica cadastrada

**Local:** `src/backend/app/services/excel_service.py:171–178`, `235–244`, `285–290`.

`fabricas_cache` não é usado para resolver a fábrica de cada pedido. Produtos e vendas novos recebem `fabrica_padrao.id`, escolhido por `.first()`, ou a fábrica artificial “Fábrica Matriz”. Na atualização de vendas, a fábrica nem sequer é atualizada.

**Evidência:** importar dois pedidos sintéticos de fábricas diferentes criou somente “Fábrica Matriz”. Nos arquivos locais, a coluna correspondente aparece como `representada`, nome que o mapeador também não reconhece como `fabrica`.

**Impacto:** rankings, mix, recomendações de fábricas e limites de inatividade por fábrica ficam incorretos na origem.

**Correção:** reconhecer a coluna real do ERP, resolver cada fábrica e associar produtos e pedidos à fábrica correta. Validar a consistência entre a fábrica do produto e a do pedido.

### 8. [P1] A reimportação pode apagar itens e aceitar divergências silenciosamente

**Local:** `src/backend/app/services/excel_service.py:249–309`, especialmente `283`.

Para um pedido existente, todos os itens são apagados antes de verificar se a planilha enviada contém o conjunto completo daquele pedido. Itens sem cabeçalho correspondente são ignorados porque o processamento percorre apenas `df_cab`. A mensagem de sucesso usa a quantidade de linhas lidas, sem refletir quantas foram realmente persistidas.

**Evidência sintética:** dois pedidos tinham um item cada. Reimportar os mesmos cabeçalhos com apenas o item do segundo pedido reduziu o total de dois itens para um e deixou o primeiro pedido sem itens, com sucesso.

**Evidência dos arquivos locais após o parsing atual:**

| Par de arquivos | Cabeçalhos | Linhas de itens | Pedidos do cabeçalho sem itens | Números de pedido dos itens sem cabeçalho |
| --- | ---: | ---: | ---: | ---: |
| Jan/2026 | 352 | 4.732 | 2 | 19 |
| Fev/2026 | 374 | 4.947 | 1 | 38 |
| Mar/2026 | 456 | 6.624 | 2 | 60 |
| Abr/2026 | 245 | 3.453 | 1 | 21 |
| Mai/2026 | 351 | 4.653 | 0 | 31 |
| Jun/2026 | 305 | 4.158 | 1 | 33 |
| Jul/2026 | 395 | 5.486 | 1 | 23 |
| Ago/2026 | 354 | 4.894 | 1 | 20 |
| Soma por par mensal | 2.832 | 38.947 | 9 | 245 |

As divergências podem vir dos filtros de exportação, de diferenças entre relatórios ou do parsing. A soma da última coluna representa ocorrências por par mensal, não necessariamente números distintos em todo o período. Elas precisam ser explicadas antes da gravação.

**Correção:** reconciliar as duas planilhas antes de atualizar o banco; separar substituição completa de atualização parcial; informar erros com pedido/linha e contagens efetivas. Comparar também totais financeiros e rejeitar ou justificar inconsistências.

### 9. [P1] Há credencial de banco em arquivo versionado

**Local:** `alembic.ini:89`.

A URL contém uma senha explícita e o arquivo está rastreado pelo Git. O valor não é reproduzido neste relatório. Mesmo que `env.py` use outra fonte de configuração, o segredo permanece no arquivo versionado.

**Correção:** remover a credencial da configuração versionada e carregá-la do ambiente. Se ela for válida ou já tiver sido compartilhada, substituí-la e avaliar sua presença no histórico do repositório.

## Falhas de cálculos, recomendações e consulta

### 10. [P2] Vendas sem vendedor desaparecem do resumo

**Local:** `src/backend/app/services/analises_services.py:63`, `79–82`.

O serviço admite `vendedor_id=None`, mas o `groupby` do Pandas exclui grupos com valores nulos por padrão. Isso reduz faturamento e quantidade de pedidos sem nenhum erro.

**Evidência:** duas vendas sem vendedor produziram zero linhas em `ResumoVendasGeral`, enquanto o pipeline informou sucesso.

**Correção:** preservar grupos nulos e tratar o vendedor ausente explicitamente na persistência e nos filtros.

### 11. [P2] “Último mês” inclui o mês atual e meses futuros

**Local:** `src/backend/app/services/analises_services.py:102–118`.

`venda_ult_mes` só possui limite inferior, no primeiro dia do mês anterior. Em setembro, soma agosto e setembro. A média dos seis meses usa uma janela móvel de 180 dias dividida por seis e também não limita datas futuras, dificultando a comparação entre períodos equivalentes.

**Evidência:** uma venda de R$ 100 em agosto e outra de R$ 200 em setembro resultaram em `venda_ultimo_mes=300`, quando o mês anterior fechado teria R$ 100.

**Correção:** definir intervalos com início inclusivo e fim exclusivo. Para a média, definir se são seis meses fechados, meses com compra ou uma janela móvel e usar a mesma regra na documentação e na interface.

### 12. [P2] A API elimina a justificativa e o volume das recomendações

**Local:** `src/backend/app/schemas/cliente.py:87–91`, `105`; `src/backend/app/services/colaborativo_service.py:165–173`.

O serviço retorna afinidade, classificação, volume sugerido e motivo. O schema aceita somente identificação e `score`, campo que o serviço não retorna. A serialização descarta os demais campos e envia `score=null`.

**Evidência:** uma recomendação com afinidade de 100%, volume de 10 unidades e justificativa chegou ao contrato de resposta apenas com produto, SKU, nome e score nulo.

**Correção:** alinhar o schema ao resultado do serviço e validar a resposta HTTP completa. Expor a medida com seu significado real; afinidade entre vizinhos não é automaticamente probabilidade de compra.

### 13. [P2] A associação de produtos calcula confiança e lift com pedidos excluídos

**Local:** `src/backend/app/services/associacao_service.py:27`, `39–69`.

Pedidos com um único produto são removidos antes dos cálculos. Um pedido contendo apenas o produto antecedente deve contar no denominador da confiança. Excluí-lo altera também o universo utilizado para medir suporte e lift.

**Evidência:** cinco pedidos A+B, cinco pedidos C+D e cem pedidos contendo somente A geraram uma recomendação de B com confiança de 100% e lift de 2. Considerando todos os pedidos, a confiança seria aproximadamente 4,8% e o lift 1,05; essa recomendação não passaria pelo mínimo de confiança de 20% configurado.

**Correção:** preservar o universo completo de pedidos nos denominadores e filtrar candidatos na etapa adequada. Definir também se uma lista de antecedentes significa comprar todos os produtos ou qualquer um deles: atualmente o código usa interseção, ou seja, qualquer um.

### 14. [P2] Linhas repetidas de um produto encurtam artificialmente seu ciclo

**Local:** `src/backend/app/services/cliente_service.py:217–247`, `253–278`.

Reposição e abandono contam linhas de itens como compras independentes. O mesmo produto em duas linhas do mesmo pedido adiciona intervalo zero e reduz o ciclo calculado.

**Evidência:** duas compras com intervalo de 30 dias, sendo a primeira dividida em duas linhas do mesmo produto, resultaram em ciclo de produto de 15 dias e alerta de reposição atrasada. O ciclo por fábrica permaneceu em 30 dias.

**Correção:** consolidar quantidade por pedido/produto e definir como tratar pedidos distintos no mesmo dia. Usar eventos de compra consistentes em todos os motores.

### 15. [P2] Clientes após os primeiros 300 não podem ser encontrados por nome

**Local:** `src/backend/app/services/cliente_service.py:50–77`.

A busca por razão social/nome fantasia examina somente os primeiros 300 clientes, sem ordenação ou paginação. Se houver qualquer resultado por cidade/grupo, o método retorna antes de procurar nomes, o que também pode omitir resultados válidos.

**Evidência:** uma base sintética de 301 clientes retornou lista vazia para o nome exclusivo do último cliente.

**Correção:** implementar uma estratégia de busca que cubra a carteira inteira, com paginação e resultados combinados. Caso a busca de nomes precise continuar cifrada em repouso, definir um índice de pesquisa adequado ao requisito.

### 16. [P2] Existem definições conflitantes para as mesmas tabelas analíticas

**Local:** `src/backend/app/models/cliente_analises.py:4–13`, `29–37`; `src/backend/app/models/resumo_vendas_geral.py:5–16`; `src/backend/app/models/fabrica_360.py:5–16`.

`ResumoVendasGeral` e `FabricaAnalytics` são declarados duas vezes na mesma Base, com definições diferentes. Importar as duas versões produziu `InvalidRequestError` indicando que a tabela já estava definida. O caminho atual da API não importa todas elas, mas registrar a camada analítica pode expor o conflito.

**Correção:** manter um modelo único por tabela e centralizar seus imports. Não mascarar definições divergentes com `extend_existing`.

## Integração e fidelidade dos dados

### 17. [P2] O pipeline analítico está desconectado da carga e da aplicação

**Local:** `src/backend/main.py:25–28`; `src/backend/app/api/analytics_routes.py:19–49`; `src/backend/app/services/analises_services.py:25`; `src/backend/app/services/excel_service.py:311`; `alembic/env.py:25–34`.

O router `/analytics` não está registrado. A carga não chama `processar_tudo`, e não foi encontrado outro chamador no projeto. As tabelas analíticas não têm migrações de criação e não estão registradas pelo conjunto de modelos usado por `init_db`/Alembic.

Além disso, as rotas analíticas existentes não exigem autenticação. Hoje não estão expostas; adicioná-las à aplicação sem corrigir as dependências tornaria os indicadores e alertas acessíveis sem JWT.

**Correção:** resolver os modelos duplicados, migrar as tabelas, definir quando recalcular, registrar as rotas com autenticação e adicionar filtros/paginação. Para alertas dependentes da passagem do tempo, definir atualização diária ou cálculo no momento da consulta; somente recalcular ao importar deixaria alertas desatualizados.

### 18. [P2] Informações de cliente e vendedor são descartadas ou transformadas sem recuperação

**Local:** `src/backend/app/services/excel_service.py:69–98`, `194–219`, `221–233`; `src/backend/app/models/cliente.py:23–28`.

O importador não preenche cidade, estado, CEP ou microregião. O diagnóstico com cidade/estado fornecidos resultou em ambos nulos. O serviço de IBGE não é chamado na carga. Na atualização, nome e grupo não são sincronizados; o grupo só é preenchido quando estava vazio.

O mapeador não normaliza acentos: `razão_social` não corresponde à regra de `razao`. Nos arquivos lidos, essa coluna ficou sem uso, enquanto outra coluna foi mapeada como `cliente`. Vendedores e redes são substituídos por tokens, sem um cadastro de correspondência exibível pelo usuário.

**Correção:** documentar o layout real do ERP, normalizar os nomes das colunas e separar o fluxo acadêmico de pseudonimização do fluxo operacional. Preservar identificadores e nomes que permitam ao escritório reconhecer vendedores/redes, com a proteção de acesso definida para o sistema.

### 19. [P2] Valores e datas inválidos podem virar dados aparentemente válidos

**Local:** `src/backend/app/services/excel_service.py:37–48`, `103–113`, `142–152`, `270–275`.

Valores não interpretáveis são convertidos em zero, a ausência de total cria pedidos de valor zero, e exceções ao interpretar datas podem substituir a data do pedido pela data atual. A quantidade é convertida para inteiro, truncando frações. O serviço grava diretamente os modelos e não aplica as validações positivas dos schemas de itens.

**Impacto:** erros de origem podem aparecer como redução de faturamento ou como atividade recente, ocultando clientes inativos. Nos oito cabeçalhos locais analisados não foram encontradas datas inválidas; o risco está no comportamento para novas cargas.

**Correção:** validar os campos obrigatórios e retornar erros de linha. Não substituir silenciosamente informação comercial desconhecida. Definir a unidade de medida e se quantidades fracionárias/devoluções são aceitas.

### 20. [P2] A CI usa caminhos que não existem e os testes não refletem alguns contratos

**Local:** `.github/workflows/ci.yml:32`, `39`; `tests/test_seguranca.py:6–7`, `66–67`; `tests/conftest.py:14–17`.

A CI tenta instalar `src/backend/requirements.txt` e testar `src/backend/tests/`, mas os caminhos existentes são `requirements.txt` e `tests/`. Os testes importam os nomes antigos de criptografia e esperam uma mensagem de token inválido diferente da implementação. As configurações de teste não são estabelecidas antes de importar a aplicação.

**Correção:** atualizar os caminhos, configurar segredos e banco de teste isolados antes dos imports, alinhar o contrato de erro e cobrir os cenários comerciais que reproduziram as falhas. Incluir lint/build do frontend na CI.

## Atendimento aos requisitos descritos

| Requisito | Estado observado | O que falta para uso real |
| --- | --- | --- |
| Enviar cabeçalhos e itens juntos | Backend aceita dois arquivos; frontend seleciona somente um e simula sucesso | Dois campos identificados, envio multipart, JWT, validação e resultado real |
| Dashboard de vendas, pedidos, clientes atendidos e ticket médio | Interface tem quatro cards demonstrativos e gráficos estáticos; existe um resumo parcial no backend | Endpoint agregado, clientes distintos, ticket calculado e integração |
| Filtrar por mês e vendedor | Não implementado na interface nem nos endpoints de indicadores | Filtros com limites de datas e cadastro reconhecível de vendedores |
| Produtos quentes e fábricas quentes/mais vendidas | Não implementado; analytics de fábrica fixa tendência em `ESTAVEL`, volume em zero e top produtos vazio | Definir tendência, período de comparação e calcular rankings reais |
| Clientes novos e inativos positivados | Não implementado | Identificar primeira compra e retorno após a regra de inatividade acordada |
| Cliente 360º com valor comprado e pedidos emitidos | Há dossiê parcial no backend; o menu Clientes apenas navega ao top 5 do dashboard | Tela própria, totais/período, histórico e contagem de pedidos |
| Produtos entrando em inatividade e reposição | Existem regras de ciclo e abandono | Corrigir eventos de compra, validar limiares e apresentar ações na tela |
| Completar mix | Há recomendação colaborativa | Corrigir contrato de resposta, mostrar motivo e validar recomendações em histórico separado |
| Sugerir fábricas | Campos analíticos são preenchidos com listas vazias | Motor de sugestão de fábricas e respectiva resposta/tela |
| Data limite de inatividade por fábrica | Dossiê calcula última compra + 90 dias | Corrigir associação de fábrica e definir se o prazo varia por fábrica |
| Agrupar Cliente 360º por rede | Recomendações e parte da recompra usam grupo; histórico do dossiê filtra um único `cliente_id` | Modo individual/rede consistente para totais, ciclos, alertas e sugestões |
| Central de alertas | Não há tela; endpoint da home cobre produtos de alto volume com pelo menos duas datas de compra | Central com todos os tipos, filtros, prioridade e acompanhamento das ações |
| Contato para segundo pedido | Não há regra funcional; campos correspondentes são listas vazias | Detectar cliente com uma compra e determinar o prazo do contato |
| Fábrica próxima da inatividade | Regra parcial no dossiê; central não a agrega | Alertar antes da data limite e distinguir ciclo de compra de inatividade |
| Produto que o cliente deixou de comprar | Abandono parcial no dossiê; alerta global agrega redes | Definir escopo cliente/rede e não ocultar a inatividade de uma filial por compras de outra |
| Autenticação real | Backend possui JWT e aprovação; frontend aceita qualquer senha não vazia | Integrar OAuth2, manter sessão e tratar expiração/perfis |
| Recuperação de senha | Simulação no frontend; endpoint correspondente ausente | Fluxo real de token, validade e troca de senha |
| Histórico de importação | Dados fixos e estado local no frontend | Persistir carga, usuário, arquivos, horário, contagens e erros no backend |

## Outros ajustes observados

- **Identidade de pedidos e produtos:** `Venda.numero_pedido` e `Produto.sku` são únicos globalmente (`models/venda.py:10`, `models/produto.py:12`). Confirmar se o ERP garante essa unicidade entre fábricas. Caso contrário, a carga pode atualizar o pedido de outra fábrica ou reutilizar um produto incorreto. O parser de SKU também divide no primeiro hífen (`excel_service.py:130`), o que precisa ser revisto se códigos alfanuméricos com hífen forem admitidos.
- **Dinheiro:** os modelos usam `Float` para valores comerciais. Para totais e conciliação, padronizar `Numeric`/`Decimal` e uma regra de arredondamento.
- **Criptografia e busca:** comparar `Cliente.cnpj_cpf == grupo_alvo` em `recompra_service.py:137` não é uma busca exata confiável sobre Fernet, pois a cifra muda a cada gravação. Utilizar o hash ou IDs de clientes no fallback de grupos. `BLIND_INDEX_SALT` aparece no `.env.example`, mas não é um campo de `Settings`; na implementação atual o fallback é `SECRET_KEY`.
- **Tamanho dos campos cifrados:** `EncryptedString(512)` limita o tamanho do token, não do texto original. Textos UTF-8 com muitos caracteres acentuados podem gerar tokens maiores que a coluna mesmo respeitando o máximo de caracteres do schema. Preferir `Text` ou definir limites compatíveis com os bytes cifrados.
- **Data de criação do usuário:** `models/usuario.py:16` avalia `datetime.now(...)` ao carregar o módulo. O default precisa ser uma função para que cada cadastro receba seu horário de criação.
- **Configuração:** `main.py:19` usa origem universal em vez de `settings.CORS_ORIGINS`. Há URLs com sintaxe de link Markdown no `.env.example:5`. O serviço de e-mail é construído ao importar as rotas, mas o valor padrão de `MAIL_FROM` é vazio; definir como a aplicação deve funcionar sem SMTP configurado.
- **Cadastro e envio de e-mail:** o usuário é confirmado no banco antes de enviar a aprovação (`auth_service.py:49`, `api/auth.py:62`). Falha de SMTP deixa um cadastro pendente, enquanto a requisição falha e uma nova tentativa encontra e-mail já cadastrado. Implementar reenvio ou uma fila de entrega. Escapar os valores interpolados no HTML do e-mail.
- **Carga:** a API não limita tamanho/quantidade de linhas, embora o frontend anuncie 10 MB. Diferenciar erros de entrada de falhas internas e evitar devolver detalhes brutos de exceções ao cliente. A sanitização de fórmulas deve ser aplicada no contexto adequado, sem alterar identificadores comerciais durante a leitura.
- **Desempenho:** recomendações e alertas carregam o histórico inteiro; o pipeline consulta vendas e itens repetidamente por cliente. Medir com o volume esperado e definir agregações/cache e paginação antes de crescer a carteira.
- **Dependências/documentação:** `requests` é usado pelo IBGE sem declaração direta em `requirements.txt`; o backend não tem versões travadas. O README principal descreve JWT como ausente e rotas não registradas, embora autenticação, clientes e carga já estejam registrados.
- **Planilhas versionadas:** os 16 arquivos em `data/raw` estão rastreados. A transformação aplicada pelo importador ocorre depois da leitura e não protege os arquivos de origem no Git. Conferir se eles são sintéticos, conforme afirma `data/README.md`, antes de compartilhar o repositório.

## Verificação executada

| Verificação | Resultado |
| --- | --- |
| `python -m pytest tests -q -p no:cacheprovider` no ambiente virtual existente | Falhou ao carregar `conftest.py`, antes de coletar testes: `settings` indefinido |
| `python scripts/verificar_imports.py` | Encontrou imports inexistentes de `encrypt_data` e `decrypt_data` nos testes |
| Parsing de sintaxe dos fontes Python | Sem erro de sintaxe; isso não elimina os erros de nomes/imports descritos |
| Cenários sintéticos em SQLite em memória | Reproduziram fábrica incorreta, localização perdida, perda de itens, resumo sem vendas, período incorreto, perda de campos da recomendação, ciclo reduzido, associação distorcida e busca limitada |
| Imports das duas versões de modelos analíticos | Reproduziram conflitos de tabelas na mesma Base |
| Suite com configuração sintética e aliases injetados apenas em memória | 13 passaram, 1 falhou na expectativa de mensagem do token de aprovação |
| Leitura dos oito pares XLS pelo importador atual | 2.832 cabeçalhos e 38.947 linhas de itens; divergências descritas na tabela |
| Lint do frontend | Passou |
| Build do frontend | Passou |

A execução diagnóstica injetou `settings` no módulo do banco e aliases de criptografia exclusivamente em memória para permitir investigar os problemas posteriores. Isso **não** significa que a suite original passou nem que esses defeitos foram corrigidos. A configuração usou banco SQLite em memória, chaves temporárias e SMTP simulado; não houve envio de e-mail nem atualização do PostgreSQL.

O ambiente Python existente é 3.14.3; a matriz da CI declara 3.11 e 3.12, que não foram executados nesta revisão. O frontend foi verificado com Node 24.19.0 e dependências instaladas via pnpm dentro das faixas do `package.json`, incluindo React 19.3.0 e Vite 8.3.1. A instalação exata do `package-lock.json` com `npm ci` não foi validada. Não foi realizado teste visual no navegador ou teste de migrações em PostgreSQL.

## Ordem recomendada de trabalho

1. Restaurar a execução: configuração do banco, nomes de criptografia, launcher e CI.
2. Tornar o esquema reproduzível e planejar a conversão dos dados existentes, removendo o `stamp` automático.
3. Corrigir o contrato da importação: fábricas, identificadores, nomes/localidades, reconciliação e reimportação sem perda de dados.
4. Corrigir cálculos e contratos de API; integrar o resumo analítico com autenticação e filtros.
5. Conectar autenticação, carga de dois arquivos e dashboard a dados reais.
6. Completar Cliente 360º e Central de Alertas, com regras comerciais acordadas e casos de teste de rede, segundo pedido e reativação.
7. Avaliar as recomendações com separação temporal: gerar sugestões com dados anteriores e verificar compras posteriores, evitando usar o futuro para validar o próprio motor.

Antes de implementar novos cards, definir por escrito o significado de “quente”, o prazo de inatividade de cada fábrica, o critério de cliente reativado, o período dos indicadores, o escopo de rede/filial e o tratamento de cancelamentos/devoluções. Essas decisões afetam a confiabilidade do produto tanto quanto o código.
