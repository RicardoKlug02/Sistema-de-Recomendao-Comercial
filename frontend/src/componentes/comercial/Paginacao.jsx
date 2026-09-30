// O tamanho vem do contrato de cada endpoint: clientes (30) e alertas (50).
export default function Paginacao({
  pagina,
  total,
  tamanho,
  aoMudar,
  carregando = false,
  unidade = 'resultados',
}) {
  const paginas = Math.max(1, Math.ceil(total / tamanho))
  return (
    <nav className="paginacao-importacao" aria-label="Paginação">
      <span>
        {total} {unidade} · Página {pagina} de {paginas}
      </span>
      <div>
        <button
          className="botao-secundario"
          disabled={carregando || pagina <= 1}
          onClick={() => aoMudar(pagina - 1)}
        >
          Anterior
        </button>
        <button
          className="botao-secundario"
          disabled={carregando || pagina >= paginas}
          onClick={() => aoMudar(pagina + 1)}
        >
          Próxima
        </button>
      </div>
    </nav>
  )
}
