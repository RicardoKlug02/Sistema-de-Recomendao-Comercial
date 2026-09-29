import { useId } from 'react'
import Icone from './Icone'

// Busca e filtros sempre informam o conjunto ao qual se aplicam.
export default function FiltrosCarteira({
  busca,
  aoBuscar,
  campos = [],
  rotulo = 'Buscar',
  dica = 'Cliente ou produto',
}) {
  const identificador = useId()
  return (
    <div className="barra-filtros" role="search" aria-label={rotulo}>
      <label className="filtro-busca" htmlFor={`${identificador}-busca`}>
        <span>{rotulo}</span>
        <div>
          <Icone nome="busca" tamanho={17} />
          <input
            id={`${identificador}-busca`}
            type="search"
            placeholder={dica}
            value={busca}
            onChange={(evento) => aoBuscar(evento.target.value)}
          />
        </div>
      </label>
      {campos.map(({ nome, titulo, valor, opcoes, aoAlterar }) => (
        <label key={nome} htmlFor={`${identificador}-${nome}`}>
          <span>{titulo}</span>
          <select
            id={`${identificador}-${nome}`}
            value={valor}
            onChange={(evento) => aoAlterar(evento.target.value)}
          >
            {opcoes.map((opcao) => (
              <option key={opcao.valor} value={opcao.valor}>
                {opcao.rotulo}
              </option>
            ))}
          </select>
        </label>
      ))}
      {busca && (
        <button className="botao-limpar" onClick={() => aoBuscar('')}>
          Limpar busca
        </button>
      )}
    </div>
  )
}
