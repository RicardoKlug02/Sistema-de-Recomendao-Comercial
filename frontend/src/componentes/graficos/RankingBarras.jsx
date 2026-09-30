import { formatarMoeda } from '../../servicos/dadosPainel'

// A escala relativa compara valores reais; não calcula percentuais de crescimento.
export default function RankingBarras({
  itens = [],
  aoSelecionar,
  vazio = 'Sem vendas no período.',
}) {
  const maior = Math.max(1, ...itens.map((item) => Number(item.valor)))
  if (!itens.length) return <p className="texto-vazio">{vazio}</p>
  return (
    <ol className="ranking-barras" tabIndex={0} aria-label="Ranking de vendas">
      {itens.map((item, indice) => (
        <li key={item.chave ?? item.id ?? `${item.nome}-${indice}`}>
          <div className="ranking-rotulo">
            <span className="ranking-posicao">
              {String(indice + 1).padStart(2, '0')}
            </span>
            {aoSelecionar ? (
              <button
                className="botao-detalhes"
                onClick={() => aoSelecionar(item.id)}
              >
                {item.nome}
              </button>
            ) : (
              <span>{item.nome}</span>
            )}
            <strong>{formatarMoeda(item.valor)}</strong>
          </div>
          <div className="ranking-trilho" aria-hidden="true">
            <span
              style={{
                width: `${(Math.max(0, Number(item.valor)) / maior) * 100}%`,
              }}
            />
          </div>
          {item.detalhe && <small>{item.detalhe}</small>}
        </li>
      ))}
    </ol>
  )
}
