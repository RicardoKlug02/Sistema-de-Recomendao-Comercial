import { solicitarApi } from './api.js'
export const tamanhoMaximo = 10 * 1024 * 1024

export function validarArquivo(arquivo) {
  if (!arquivo) return 'Selecione as duas planilhas para importar.'
  if (!/\.(xls|xlsx)$/i.test(arquivo.name)) return 'Selecione uma planilha XLS ou XLSX.'
  if (arquivo.size === 0) return 'O arquivo está vazio.'
  if (arquivo.size > tamanhoMaximo) return 'Cada arquivo deve ter no máximo 10 MB.'
  return ''
}

export async function importarArquivos(pedidos, itens, signal) {
  const erro = validarArquivo(pedidos) || validarArquivo(itens)
  if (erro) throw new Error(erro)
  const formulario = new FormData()
  formulario.append('arquivo_cabecalho', pedidos)
  formulario.append('arquivo_itens', itens)
  const resposta = await solicitarApi('/cargas/excel', {
    method: 'POST',
    body: formulario,
    prazo: 180000,
    signal,
  })
  if (resposta.status === 'erro')
    throw new Error(resposta.mensagem || 'O servidor não conseguiu importar as planilhas.')
  return resposta
}
