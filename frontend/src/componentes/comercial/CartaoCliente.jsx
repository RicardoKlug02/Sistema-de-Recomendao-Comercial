import Icone from './Icone'

export default function CartaoCliente({ cliente, aoAbrir }) {
  return (
    <article className="cartao cartao-cliente">
      <div className="topo-cliente">
        <span className="avatar">
          <Icone nome="clientes" />
        </span>
        <span className="etiqueta etiqueta-neutra">
          {cliente.grupo_economico ? 'Rede de clientes' : 'Cliente individual'}
        </span>
      </div>
      <h2>{cliente.razao_social}</h2>
      <p className="local-cliente">
        <Icone nome="local" tamanho={15} />
        {[cliente.cidade, cliente.estado].filter(Boolean).join(' · ') ||
          'Localização não informada'}
      </p>
      <p className="rede-cliente">
        {cliente.grupo_economico || 'Sem grupo econômico'}
      </p>
      <button className="botao-abrir" onClick={() => aoAbrir(cliente.id)}>
        Abrir ficha <Icone nome="seta" tamanho={17} />
      </button>
    </article>
  )
}
