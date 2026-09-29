import Etiqueta from './Etiqueta'
import Icone from './Icone'

// Explica o sinal e a próxima ação sem atribuir compras externas ao cliente.
export default function CartaoOportunidade({ oportunidade, cliente, aoAbrirCliente }) {
  return (
    <article className="cartao cartao-oportunidade">
      <div className="linha-cartao">
        <span className="tipo-oportunidade">
          <Icone nome="oportunidade" tamanho={15} />
          {oportunidade.tipo}
        </span>
        <Etiqueta texto={oportunidade.prioridade} />
      </div>
      <h3>{oportunidade.titulo}</h3>
      <p className="nome-oportunidade">{cliente.nome}</p>
      <p className="motivo-oportunidade">{oportunidade.motivo}</p>
      <p className="evidencia-oportunidade">{oportunidade.evidencia}</p>
      <div className="acao-sugerida">
        <span>PRÓXIMO PASSO</span>
        <p>{oportunidade.acao}</p>
      </div>
      <footer>
        <span>{oportunidade.sku ? `SKU ${oportunidade.sku}` : 'Alerta de recompra'}</span>
        <button className="botao-detalhes" onClick={() => aoAbrirCliente(cliente)}>
          Ver cliente <Icone nome="seta" tamanho={16} />
          <span className="somente-leitor">: {cliente.nome}</span>
        </button>
      </footer>
    </article>
  )
}
