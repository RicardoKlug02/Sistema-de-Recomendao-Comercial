import Icone from './Icone'

// A busca não fornece faturamento ou situação; esses dados não são inferidos aqui.
export default function CartaoCliente({ cliente, aoAbrirCliente }) {
  return (
    <article className="cartao cartao-cliente">
      <span className="avatar-cliente" aria-hidden="true">
        {cliente.nome
          .split(' ')
          .slice(0, 2)
          .map((parte) => parte[0])
          .join('')
          .toUpperCase()}
      </span>
      <h2>{cliente.nome}</h2>
      <p className="local-cliente">
        <Icone nome="local" tamanho={14} />
        {cliente.cidade || 'Cidade não informada'}
        {cliente.estado ? ` · ${cliente.estado}` : ''}
      </p>
      <dl className="metricas-cliente">
        <div>
          <dt>Nome fantasia</dt>
          <dd>{cliente.fantasia || 'Não informado'}</dd>
        </div>
        <div>
          <dt>CNPJ / CPF</dt>
          <dd>{cliente.documento || 'Não informado'}</dd>
        </div>
      </dl>
      <p className="fabricas-cliente">
        <span>Grupo econômico</span>
        {cliente.grupo || 'Não informado'}
      </p>
      <footer>
        <span>Histórico e recomendações</span>
        <button className="botao-detalhes" onClick={() => aoAbrirCliente(cliente)}>
          Ver perfil <Icone nome="seta" tamanho={16} />
          <span className="somente-leitor">: {cliente.nome}</span>
        </button>
      </footer>
    </article>
  )
}
