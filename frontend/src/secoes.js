export const secoes = [
  { id: 'painel', titulo: 'Visão geral' },
  { id: 'clientes', titulo: 'Clientes' },
  { id: 'alertas', titulo: 'Alertas' },
  { id: 'relatorios', titulo: 'Relatórios' },
  { id: 'analise', titulo: 'Análise do sistema' },
  { id: 'regras', titulo: 'Regras de negócio' },
  { id: 'importacoes', titulo: 'Importação', restrita: true },
  { id: 'usuarios', titulo: 'Usuários', restrita: true },
]

export const tituloSecao = (id) => secoes.find((s) => s.id === id).titulo
export const tituloDocumento = (titulo) => `${titulo} | Rio Verde Representações`
