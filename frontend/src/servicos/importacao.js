import { solicitar } from './api'

const tamanhoMaximo = 10 * 1024 * 1024
const tempoLimite = 180000

function validarArquivo(arquivo) {
  if (!arquivo) return 'Selecione as duas planilhas.'
  if (!/\.(xls|xlsx)$/i.test(arquivo.name)) return 'Envie XLS ou XLSX.'
  if (!arquivo.size || arquivo.size > tamanhoMaximo) return 'Cada arquivo deve ter entre 1 byte e 10 MB.'
  return ''
}
function montarEnvio(cabecalho, itens) {
  const erro = validarArquivo(cabecalho) || validarArquivo(itens)
  if (erro) throw new Error(erro)
  const dados = new FormData()
  dados.append('arquivo_cabecalho', cabecalho)
  dados.append('arquivo_itens', itens)
  return dados
}

export async function conferirPlanilhas(cabecalho, itens) {
  return solicitar('/cargas/conferir', { method: 'POST', body: montarEnvio(cabecalho, itens), tempoLimite })
}

export async function confirmarImportacao(cabecalho, itens, tokenConferencia) {
  const dados = montarEnvio(cabecalho, itens)
  dados.append('token_conferencia', tokenConferencia)
  dados.append('vendas_comissao', 'true')
  return solicitar('/cargas/excel', { method: 'POST', body: dados, tempoLimite })
}
