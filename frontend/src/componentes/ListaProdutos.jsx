import { useId, useState } from 'react'
import { filtrarProdutos } from '../servicos/busca'

// Os mesmos filtros e limites atendem às listas e às tabelas de produtos.
export default function ListaProdutos({ produtos, renderizarItem, renderizarLista, inicial = 5, incremento = 10,
  situacoes = [], filtrarSituacao = (p, s) => p.status === s,
  rotuloSituacao = 'Situação', todasSituacoes = 'Todas as situações' }) {
  const id = useId()
  const conteudoId = `${id}-resultados`
  const [termo, definirTermo] = useState('')
  const [fabrica, definirFabrica] = useState('')
  const [situacao, definirSituacao] = useState('')
  const [limite, definirLimite] = useState(inicial)
  const fabricas = [...new Set(produtos.map((p) => p.fabrica).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
  const fabricaAtiva = fabricas.includes(fabrica) ? fabrica : ''
  const encontrados = filtrarProdutos(produtos, termo).filter((p) =>
    (!fabricaAtiva || p.fabrica === fabricaAtiva) && (!situacao || filtrarSituacao(p, situacao)))
  const visiveis = encontrados.slice(0, limite)
  const restantes = encontrados.length - limite
  function limpar() {
    definirTermo(''); definirFabrica(''); definirSituacao(''); definirLimite(inicial)
  }
  return <>
    {(produtos.length > inicial || fabricas.length > 1 || situacoes.length > 0) && <div className="filtros-lista-produtos">
      <div className="busca-lista">
        <label htmlFor={id}>Buscar por código, nome ou fábrica</label>
        <input id={id} type="search" value={termo} placeholder="Ex.: 1020 ou tomada mec tronic"
          onChange={(e) => { definirTermo(e.target.value); definirLimite(inicial) }} />
      </div>
      {fabricas.length > 1 && <label htmlFor={`${id}-fabrica`}>Fábrica dos produtos
        <select id={`${id}-fabrica`} value={fabricaAtiva} onChange={(e) => { definirFabrica(e.target.value); definirLimite(inicial) }}>
          <option value="">Todas as fábricas</option>
          {fabricas.map((nome) => <option key={nome} value={nome}>{nome}</option>)}
        </select>
      </label>}
      {situacoes.length > 0 && <label htmlFor={`${id}-situacao`}>{rotuloSituacao}
        <select id={`${id}-situacao`} value={situacao} onChange={(e) => { definirSituacao(e.target.value); definirLimite(inicial) }}>
          <option value="">{todasSituacoes}</option>
          {situacoes.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
        </select>
      </label>}
      {(termo || fabricaAtiva || situacao) && <button type="button" className="botao-texto" onClick={limpar}>Limpar filtros</button>}
    </div>}
    <p className="total-lista-produtos" aria-live="polite">Mostrando {visiveis.length} de {encontrados.length} produtos{encontrados.length !== produtos.length ? ` (${produtos.length} no total)` : ''}.</p>
    <div id={conteudoId}>{encontrados.length
      ? renderizarLista ? renderizarLista(visiveis) : <ul>{visiveis.map(renderizarItem)}</ul>
      : <p>{termo ? `Nenhum produto encontrado para “${termo}”.` : 'Nenhum produto encontrado para os filtros selecionados.'}</p>}</div>
    <div className="acoes-lista">
      {restantes > 0 && <button type="button" className="botao-secundario" aria-controls={conteudoId} onClick={() => definirLimite(Math.min(limite + incremento, encontrados.length))}>
        Mostrar mais ({restantes})
      </button>}
      {limite > inicial && encontrados.length > inicial && <button type="button" className="botao-texto" aria-controls={conteudoId} onClick={() => definirLimite(inicial)}>
        Mostrar menos
      </button>}
    </div>
  </>
}
