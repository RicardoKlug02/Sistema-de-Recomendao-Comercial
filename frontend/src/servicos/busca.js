const normalizar = (texto) => String(texto ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function filtrarProdutos(produtos, termo) {
  const busca = normalizar(termo).trim()
  if (!busca) return produtos
  return produtos.filter((p) => normalizar(p.sku).includes(busca) || normalizar(p.nome).includes(busca))
}
