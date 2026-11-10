export const tiposAlerta = {
  SEGUNDO_PEDIDO: 'Segundo pedido na base',
  CLIENTE_INATIVO: 'Cliente inativo',
  FABRICA_EM_RISCO: 'Fábrica próxima da inatividade',
  FABRICA_INATIVA: 'Fábrica inativa',
  PRODUTO_EM_RISCO: 'Produto em risco',
}

export const situacoesAcompanhamento = { PENDENTE: 'Pendente', CONTATADO: 'Contatado', AGUARDANDO_RETORNO: 'Aguardando retorno', DISPENSADO: 'Dispensado', RECOMPRA_REALIZADA: 'Recompra realizada (informada)', PRODUTO_DESCONTINUADO: 'Produto descontinuado (informado)' }

export const permiteProximoContato = (situacao) => ['CONTATADO', 'AGUARDANDO_RETORNO'].includes(situacao)

export function proximaAcao(resumo = {}) {
  if (resumo.CLIENTE_INATIVO || resumo.FABRICA_INATIVA) return 'Revisar oportunidades de retorno.'
  if (resumo.SEGUNDO_PEDIDO) return 'Verificar o contato após a primeira compra registrada na base.'
  return 'Conferir o histórico e preparar o próximo contato.'
}
