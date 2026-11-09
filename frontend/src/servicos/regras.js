import { dataLocal } from './formatacao'

export const tiposRegra = { SUBSTITUICAO: 'Substituição de produto', RESTRICAO: 'Restrição de venda da fábrica' }
export const ufs = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ')

export function regraVazia() {
  return { tipo: 'SUBSTITUICAO', fabrica_id: '', cliente_id: '', uf: '', codigo_antigo: '', codigo_novo: '', unificar_historico: true,
    excecoes_clientes: [], excecoes_vendedores: [], excecoes_clientes_detalhes: [], inicio: dataLocal(), fim: '', ativa: true, motivo: '' }
}

export function regraParaApi(r) {
  const restricao = r.tipo === 'RESTRICAO'
  const substituicao = r.tipo === 'SUBSTITUICAO'
  return { tipo: r.tipo, fabrica_id: Number(r.fabrica_id), cliente_id: r.cliente_id ? Number(r.cliente_id) : null,
    uf: restricao ? r.uf || null : null,
    codigo_antigo: substituicao ? r.codigo_antigo : null,
    codigo_novo: substituicao ? r.codigo_novo : null,
    unificar_historico: r.unificar_historico ?? true,
    excecoes_clientes: restricao ? r.excecoes_clientes || [] : [],
    excecoes_vendedores: restricao ? r.excecoes_vendedores || [] : [],
    inicio: r.inicio, fim: r.fim || null, ativa: r.ativa, motivo: r.motivo }
}

export function situacaoRegra(r, hoje = dataLocal()) {
  if (!r.ativa) return 'Desativada'
  if (r.inicio > hoje) return 'Agendada'
  if (r.fim && r.fim < hoje) return 'Encerrada'
  return 'Em vigor'
}
