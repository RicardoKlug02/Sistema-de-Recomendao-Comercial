import { formatarMoeda } from '../../servicos/dadosPainel'

// Barras CSS: sem biblioteca adicional. Cada valor permanece acessível por teclado e leitor de tela.
export default function GraficoMensal({ dados = [], mesSelecionado }) {
  const maior = Math.max(1, ...dados.map((item) => Number(item.valor)))
  if (!dados.length)
    return <p className="texto-vazio">Ainda não há histórico de faturamento.</p>
  return (
    <div className="area-grafico">
      <div
        className="grafico-colunas"
        role="list"
        aria-label="Faturamento por mês"
      >
        {dados.map((item) => (
          <div
            className={`coluna-mensal ${item.mes === mesSelecionado ? 'selecionada' : ''}`}
            role="listitem"
            tabIndex={0}
            key={item.mes}
            aria-label={`${item.mes}: ${formatarMoeda(item.valor)}`}
          >
            <span className="valor-coluna">{formatarMoeda(item.valor)}</span>
            <div className="trilho-coluna" aria-hidden="true">
              <span
                style={{
                  height: `${(Math.max(0, Number(item.valor)) / maior) * 100}%`,
                }}
              />
            </div>
            <span>
              {item.mes.slice(5)}/{item.mes.slice(2, 4)}
            </span>
          </div>
        ))}
      </div>
      <p className="legenda-grafico">
        <span /> Faturamento mensal <span className="legenda-selecionada" />{' '}
        Período selecionado
      </p>
    </div>
  )
}
