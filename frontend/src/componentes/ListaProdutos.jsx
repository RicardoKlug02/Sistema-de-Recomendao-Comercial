import { useId, useState } from 'react'
import { filtrarProdutos } from '../servicos/busca'

// Mostra os primeiros itens e libera o restante aos poucos; a busca só aparece quando a lista é longa.
export default function ListaProdutos({ produtos, renderizarItem, inicial = 5, incremento = 10 }) {
  const id = useId()
  const [termo, definirTermo] = useState('')
  const [limite, definirLimite] = useState(inicial)
  const encontrados = filtrarProdutos(produtos, termo)
  const restantes = encontrados.length - limite
  return <>
    {produtos.length > inicial && <div className="busca-lista">
      <label htmlFor={id}>Buscar por código ou nome</label>
      <input id={id} type="search" value={termo} placeholder="Ex.: 1020 ou tomada mec tronic"
        onChange={(e) => { definirTermo(e.target.value); definirLimite(inicial) }} />
    </div>}
    {encontrados.length
      ? <ul>{encontrados.slice(0, limite).map(renderizarItem)}</ul>
      : <p>Nenhum produto encontrado para “{termo}”.</p>}
    <div className="acoes-lista">
      {restantes > 0 && <button type="button" className="botao-secundario" onClick={() => definirLimite(limite + incremento)}>
        Mostrar mais ({restantes})
      </button>}
      {limite > inicial && encontrados.length > inicial && <button type="button" className="botao-texto" onClick={() => definirLimite(inicial)}>
        Mostrar menos
      </button>}
    </div>
  </>
}
