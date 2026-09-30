import { solicitar } from './api'
export const tamanhoMaximo = 10 * 1024 * 1024
export function validarArquivo(arquivo) {
  if (!arquivo) return 'Selecione as duas planilhas.'
  if (!/\.(xls|xlsx)$/i.test(arquivo.name)) return 'Envie XLS ou XLSX.'
  if (!arquivo.size || arquivo.size > tamanhoMaximo) return 'Cada arquivo deve ter entre 1 byte e 10 MB.'
  return ''
}
export async function importarArquivos(cabecalho, itens, token) {
  const erro = validarArquivo(cabecalho) || validarArquivo(itens)
  if (erro) throw new Error(erro)
  const dados = new FormData()
  dados.append('arquivo_cabecalho', cabecalho)
  dados.append('arquivo_itens', itens)
  if (token) {
    dados.append('token_conferencia', token)
    dados.append('vendas_comissao', 'true')
  }
  return solicitar(token ? '/cargas/excel' : '/cargas/conferir', { method: 'POST', body: dados, tempoLimite: 180000 })
}
