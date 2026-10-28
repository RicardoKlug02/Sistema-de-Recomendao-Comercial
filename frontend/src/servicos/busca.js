const normalizar = (texto) => String(texto ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()

export function filtrarProdutos(produtos, termo) {
  const termos = normalizar(termo).trim().split(/\s+/).filter(Boolean)
  if (!termos.length) return produtos
  return produtos.filter((p) => {
    const conteudo = normalizar(`${p.sku ?? ''} ${p.nome ?? ''} ${p.fabrica ?? ''}`)
    return termos.every((termo) => conteudo.includes(termo))
  })
}

export function correspondeVariacao(produto, filtro) {
  if (!filtro) return true
  const valor = produto.variacao_pct
  const comparavel = produto.status === 'COMPARAVEL' && Number.isFinite(valor)
  if (filtro === 'sem_comparacao') return !comparavel
  if (!comparavel) return false
  if (filtro === 'queda') return valor < 0
  if (filtro === 'aumento') return valor > 0
  if (filtro === 'estavel') return valor === 0
  return false
}
