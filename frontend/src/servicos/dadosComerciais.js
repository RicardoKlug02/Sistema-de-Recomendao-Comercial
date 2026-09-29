// Apenas formatação e adaptação dos contratos publicados; sem dados fictícios.
export const formatarMoeda = (valor) =>
  typeof valor === 'number' && Number.isFinite(valor)
    ? valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
    : 'Não disponível'
export const normalizarTexto = (texto) =>
  (texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
export const formatarNumero = (valor) => (typeof valor === 'number' ? valor.toLocaleString('pt-BR') : '—')

export function adaptarAlerta(alerta, indice) {
  const critico = normalizarTexto(alerta.status).includes('critico')
  return {
    id: `${alerta.cliente_id}-${alerta.produto_id}-${indice}`,
    cliente: { id: alerta.cliente_id, nome: alerta.razao_social || 'Cliente não informado' },
    produto: alerta.nome_produto || 'Produto não informado',
    sku: alerta.sku,
    tipo: critico ? 'Reativação' : 'Reposição',
    prioridade: critico ? 'Alta' : 'Média',
    titulo: critico ? 'Retomar uma compra recorrente' : 'Conferir a próxima reposição',
    motivo: `${alerta.nome_produto || 'Produto'}: ${formatarNumero(alerta.dias_atraso)} dias de atraso em relação ao ciclo de compra.`,
    acao: critico
      ? 'Conversar com o cliente e entender a pausa nas compras.'
      : 'Confirmar a necessidade e preparar uma proposta de reposição.',
    evidencia: `Ciclo de ${formatarNumero(alerta.periodicidade_dias)} dias e volume médio de ${formatarNumero(alerta.volume_medio_pedido)} unidades por pedido.`,
    status: alerta.status || 'Não informado',
  }
}

export function adaptarCliente(cliente) {
  return {
    id: cliente.id,
    nome: cliente.razao_social,
    fantasia: cliente.nome_fantasia,
    documento: cliente.cnpj_cpf,
    grupo: cliente.grupo_economico,
    cidade: cliente.cidade,
    estado: cliente.estado,
  }
}
