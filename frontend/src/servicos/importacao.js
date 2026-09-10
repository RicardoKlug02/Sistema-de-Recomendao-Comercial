export const tamanhoMaximo = 10 * 1024 * 1024

// Os exemplos ficam separados da tela para facilitar a integração com o backend.
export const historicoInicial = [
  { id: 1, arquivo: 'dados_comerciais_agosto2026.xlsx', data: '2026-08-26', usuario: 'Carlos Silva', processados: 1247, adicionados: 312, atualizados: 893, erros: 42 },
  { id: 2, arquivo: 'produtos_atualizacao_jul2026.xlsx', data: '2026-07-18', usuario: 'Carlos Silva', processados: 856, erros: 0 },
  { id: 3, arquivo: 'clientes_novos_jul2026.xlsx', data: '2026-07-05', usuario: 'Ana Rodrigues', processados: 234, erros: 12 },
  { id: 4, arquivo: 'pedidos_junho2026.xlsx', data: '2026-06-28', usuario: 'Carlos Silva', processados: 2103, erros: 0 },
  { id: 5, arquivo: 'dados_comerciais_jun2026.xlsx', data: '2026-06-15', usuario: 'Ana Rodrigues', processados: 1890, erros: 1890 },
  { id: 6, arquivo: 'produtos_maio2026.xlsx', data: '2026-05-22', usuario: 'Carlos Silva', processados: 745, erros: 0 },
]

export function validarArquivo(arquivo) {
  if (!arquivo) return 'Selecione um arquivo para importar.'
  if (!/\.(xls|xlsx)$/i.test(arquivo.name)) return 'Selecione uma planilha no formato XLS ou XLSX.'
  if (arquivo.size === 0) return 'O arquivo está vazio. Selecione outra planilha.'
  if (arquivo.size > tamanhoMaximo) return 'O arquivo deve ter no máximo 10 MB.'
  return ''
}

export function obterSituacao(importacao) {
  if (importacao.erros === importacao.processados) return 'Erro'
  return importacao.erros ? 'Concluído com erros' : 'Concluído'
}

// Simula a espera e o resultado, sem ler nem enviar o conteúdo da planilha.
export async function importarArquivo(arquivo, usuario) {
  const erro = validarArquivo(arquivo)
  if (erro) throw new Error(erro)
  await new Promise((resolver) => setTimeout(resolver, 900))
  return {
    id: crypto.randomUUID(), arquivo: arquivo.name,
    data: new Date().toLocaleDateString('sv-SE'), usuario: usuario.email,
    processados: 1247, adicionados: 312, atualizados: 893, erros: 42,
  }
}
