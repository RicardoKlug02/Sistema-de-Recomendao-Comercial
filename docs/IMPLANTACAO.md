# Implantação no Neon e Render

## Banco e chaves

Configure no Render os valores da instalação que usa o mesmo banco. O arquivo local `.env` contém os valores desta instalação e está ignorado pelo Git.

| Variável | Valor |
| --- | --- |
| DATABASE_URL | Conexão do Neon; o endereço com pool é aceito e o driver pg8000 verifica TLS |
| SECRET_KEY | Chave de assinatura secreta |
| SECRET_ENCRYPTION_KEY | Chave Fernet base64 válida; preserve-a para ler clientes já importados |
| BLIND_INDEX_SALT | Copie o valor local, caso preenchido; caso vazio, o sistema usa SECRET_KEY |
| JWT_SECRET_KEY | Copie o valor local, caso preenchido; caso vazio, o sistema usa SECRET_KEY |
| ADMIN_EMAIL | E-mail do administrador inicial |
| ADMIN_PASSWORD | Senha inicial; usada apenas quando a conta ainda não existe |
| SERVE_FRONTEND | true |
| MAIL_ENABLED | false |
| DEBUG | false |

Preserve especialmente `SECRET_ENCRYPTION_KEY` e o segredo usado por `BLIND_INDEX_SALT` entre deploys. Trocar essas chaves em um banco preenchido impede a leitura ou a identificação dos clientes existentes. Alterar `ADMIN_PASSWORD` não redefine a senha de uma conta que já existe.

## Serviço único com Docker (alternativa)

No serviço Render conectado a este repositório, selecione runtime **Docker**, Dockerfile **./Dockerfile**, raiz do projeto vazia e health check **/health**. Configure as variáveis acima e publique a versão corrigida. Se o serviço existente for do tipo Python, crie um serviço Docker ou mantenha o fluxo Python abaixo.

O Blueprint render.yaml descreve o serviço Python existente, com buildCommand, startCommand e health check. Adicionar esse arquivo ao repositório não altera automaticamente as configurações de um serviço criado manualmente; confira-as no painel.

O Dockerfile executa `npm ci`, compila a interface e instala a API. O startup roda `alembic upgrade head`; falhas nas migrações interrompem o deploy. A porta vem de `PORT`, fornecida pelo Render.

Abra o endereço público do serviço: ele deve mostrar a tela de login. Confira `/health/ready` para verificar o acesso ao banco. Entre com o administrador e faça a nova importação em **Importação**.

## Serviço Python existente

Use os seguintes comandos. Os arquivos .python-version e .node-version fixam as famílias Python 3.12 e Node.js 22 no Render (variáveis de versão explícitas no painel têm precedência):

Build:
```sh
bash scripts/build_render.sh
```

Start:
```sh
python start.py
```

Para frontend hospedado separadamente, configure `VITE_API_URL` com a URL da API (sem `/api/v1`) antes de compilar, e `CORS_ORIGINS` na API com uma lista JSON das origens autorizadas. A configuração padrão serve ambos no mesmo endereço.

## Nova importação

1. Exporte cabeçalhos e itens com o mesmo período e filtros.
2. Cabeçalhos: Pedido, Data, Cliente/Razão Social, CNPJ/CPF, Fábrica/Representada, Valor Total; opcionais Vendedor, Cidade, Estado, CEP, Nome Fantasia e Rede/Grupo Econômico.
3. Itens: Pedido, SKU/Código, Produto/Descrição, Quantidade, Preço Unitário. O relatório por blocos `Produto:` do ERP também é aceito.
4. Se o número de pedido se repetir entre fábricas, inclua **Fábrica** na tabela de itens. A carga rejeita associação ambígua.
5. Envie os dois arquivos XLS/XLSX, até 10 MB cada, e confira o resultado e os avisos.

Pedidos sem itens são aceitos. Não são criados produtos artificiais para eles. Reimportar o mesmo pedido/fábrica atualiza o cabeçalho; quando há itens na nova carga, substitui o conjunto anterior de itens desse pedido. Envie o conjunto completo de itens de cada pedido. Reenvio sem itens conserva itens já conhecidos. Itens sem cabeçalho correspondente são ignorados com aviso; confira os filtros se isso não era esperado.

Datas e números inválidos rejeitam a carga inteira. CPF/CNPJ é obrigatório para identificar o cliente. Para redes, use o mesmo nome na coluna Rede em todas as filiais.

## Regras atuais

- Segundo pedido: cliente com apenas um pedido e pelo menos 14 dias sem nova compra.
- Fábrica: aviso aos 76 dias e inatividade aos 90 dias sem pedido.
- Cliente: inatividade após 90 dias.
- Produto: pelo menos duas datas de compra; aviso após 1,5 vez o ciclo médio, com mínimo de 30 dias.
- Recomendações: dependem do histórico conhecido de itens; uma carga sem itens não permite sugerir mix por produto.

Os alertas são calculados na consulta. A central ainda não registra tarefas concluídas nem substitui julgamento comercial sobre churn. A análise de rede soma as filiais no Cliente 360º; os alertas da central continuam por cliente para não ocultar filiais inativas.

## Plano gratuito

O [Render Free](https://render.com/docs/free) suspende serviços sem tráfego após 15 minutos e bloqueia portas SMTP usuais. A primeira visita pode demorar; a interface espera até 90 segundos (180 para importações), sem repetir automaticamente o envio de arquivos. Novos usuários podem ser aprovados na própria tela **Usuários**, sem depender de e-mail. O health check do processo não mantém o Neon ativo com consultas contínuas.

## Reset explícito

O reset nunca roda no startup. Para uma reconstrução deliberada, confira o host e execute:

```sh
python scripts/reset_db.py --confirmar --host HOST_EXATO_DO_NEON
```

Ele apaga as tabelas conhecidas deste projeto, incluindo usuários e histórico, e reconstrói o esquema. Nenhuma planilha local é excluída ou importada automaticamente. Exige configuração de administrador inicial para permitir o acesso após a reconstrução.
