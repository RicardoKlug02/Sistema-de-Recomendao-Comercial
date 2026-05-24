# Documentação da Camada de Dados

Este diretório contém os conjuntos de dados utilizados para o motor de recomendação e para a análise de indicadores (KPIs) do sistema de suporte à decisão.

## Estrutura de Diretórios
- `/raw`: Armazena os dados brutos exportados do sistema de gestão (ERP). **Não modificar.**
- `/processed`: Contém os dados após o tratamento, limpeza e enriquecimento, prontos para o consumo da aplicação.
- `/scripts`: Scripts Python para ETL (*Extract, Transform, Load*) e geração de massa de dados sintéticos.

## Origem dos Dados
Os dados foram coletados a partir da base de vendas de um escritório de representação comercial, abrangendo os seguintes pontos:
- **Pedidos:** Histórico de transações, datas e valores totais.
- **Produtos:** Cadastro de itens, categorias e preços unitários.
- **Clientes:** Informações geográficas (cidades/regiões) e histórico de compras.

## Processamento (Pipeline)
Para garantir a qualidade dos dados utilizados pelo algoritmo de Inteligência Artificial:
1. **Limpeza:** Remoção de registros duplicados e valores nulos.
2. **Transformação:** Conversão de formatos e normalização de dados geográficos.
3. **Sintetização:** Aplicação de scripts para anonimização de dados sensíveis, garantindo a conformidade com a LGPD e privacidade dos clientes.

## Observações de Segurança
* Este repositório **não** contém dados reais sensíveis (CPFs, nomes completos ou dados bancários). 
* Qualquer dado exposto aqui é sintético ou anonimizado para fins de demonstração acadêmica.

---
*Documentação criada para o Projeto de TCC - Sistemas de Informação (Ricardo Nilson Klug).*