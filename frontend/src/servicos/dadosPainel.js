// Dados demonstrativos do wireframe; substituir pelo contrato da API quando disponível.
export const dadosPainel = {
  indicadores: [
    { titulo: 'Faturamento total', valor: 'R$ 1.842.300,00', detalhe: '↑ 12% vs. período anterior' },
    { titulo: 'Total de clientes', valor: '156', detalhe: '8 novos este mês' },
    { titulo: 'Pedidos no mês', valor: '234', detalhe: '↑ 5% vs. mês anterior' },
    { titulo: 'Oportunidades ativas', valor: '47', detalhe: '12 de alta prioridade' },
  ],
  faturamentoMensal: [
    { mes: 'Ago', valor: 155000 }, { mes: 'Set', valor: 116000 },
    { mes: 'Out', valor: 142000 }, { mes: 'Nov', valor: 110000 },
    { mes: 'Dez', valor: 168000 }, { mes: 'Jan', valor: 123000 },
    { mes: 'Fev', valor: 137000 }, { mes: 'Mar', valor: 104000 },
    { mes: 'Abr', valor: 130000 }, { mes: 'Mai', valor: 149000 },
    { mes: 'Jun', valor: 162000 }, { mes: 'Jul', valor: 181000 },
  ],
  categorias: [
    { nome: 'Hidráulica', percentual: 35 }, { nome: 'Conexões', percentual: 25 },
    { nome: 'Tubulação', percentual: 20 }, { nome: 'Vedação', percentual: 12 },
    { nome: 'Fixação', percentual: 8 },
  ],
  clientes: [
    { nome: 'Hidráulica Central Ltda', faturamento: 284500 },
    { nome: 'Construtora Horizonte', faturamento: 198200 },
    { nome: 'IndTech Soluções', faturamento: 176800 },
    { nome: 'Ferreira & Cia', faturamento: 154300 },
    { nome: 'AquaFlow Sistemas', faturamento: 132100 },
  ],
  importacoes: [
    { arquivo: 'dados_comerciais_agosto2026.xlsx', data: '2026-08-26', situacao: 'Concluído', registros: 1247 },
    { arquivo: 'produtos_atualizacao_jul2026.xlsx', data: '2026-07-18', situacao: 'Concluído', registros: 856 },
    { arquivo: 'clientes_novos_jul2026.xlsx', data: '2026-07-05', situacao: 'Com erros', registros: 234 },
  ],
  oportunidades: [
    { id: 1, cliente: 'Hidráulica Central Ltda', produto: 'Conexões Hidráulicas', relevancia: 'Alta', valor: 12500 },
    { id: 2, cliente: 'Construtora Horizonte', produto: 'Vedações Industriais', relevancia: 'Média', valor: 8200 },
    { id: 3, cliente: 'IndTech Soluções', produto: 'Tubos de Aço Carbono', relevancia: 'Alta', valor: 15800 },
    { id: 4, cliente: 'Ferreira & Cia', produto: 'Abraçadeiras Metálicas', relevancia: 'Baixa', valor: 3400 },
    { id: 5, cliente: 'AquaFlow Sistemas', produto: 'Mangueiras Flexíveis', relevancia: 'Alta', valor: 9700 },
  ],
}

export function formatarMoeda(valor) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
