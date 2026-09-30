import Marca from './comercial/Marca'
import Icone from './comercial/Icone'

const itens = [
  ['painel', 'Visão geral'],
  ['clientes', 'Clientes'],
  ['alertas', 'Alertas'],
  ['importacoes', 'Importação'],
  ['usuarios', 'Usuários'],
]
const perfis = {
  admin: 'Administrador',
  gestor: 'Gestor',
  vendedor: 'Representante',
}

export default function MenuLateral({
  usuario,
  secaoAtiva,
  aoNavegar,
  aoSair,
}) {
  const gestor = ['admin', 'gestor'].includes(usuario.perfil)
  return (
    <aside className="menu-lateral">
      <a
        className="marca"
        href="#painel"
        onClick={(e) => {
          e.preventDefault()
          aoNavegar('painel')
        }}
      >
        <Marca />
      </a>
      <p className="legenda-menu">ESPAÇO COMERCIAL</p>
      <nav aria-label="Menu principal">
        {itens
          .filter(([id]) => gestor || !['usuarios', 'importacoes'].includes(id))
          .map(([id, titulo]) => (
            <a
              key={id}
              href={`#${id}`}
              aria-current={secaoAtiva === id ? 'page' : undefined}
              onClick={(e) => {
                e.preventDefault()
                aoNavegar(id)
              }}
            >
              <Icone nome={id} tamanho={19} />
              {titulo}
              <span className="ponto-menu" />
            </a>
          ))}
      </nav>
      <div className="nota-menu">
        <Icone nome="oportunidade" />
        <strong>
          Boas vendas começam
          <br />
          com boas informações.
        </strong>
        <p>Sua carteira, mais próxima.</p>
      </div>
      <div className="rodape-menu">
        <div className="perfil">
          <span className="avatar" aria-hidden="true">
            {(usuario.nome || usuario.email || 'RV').slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong>{usuario.nome || usuario.email}</strong>
            <small>{perfis[usuario.perfil] || 'Colaborador'}</small>
          </div>
        </div>
        <button className="botao-sair" onClick={aoSair}>
          Sair da conta <Icone nome="sair" tamanho={17} />
        </button>
      </div>
    </aside>
  )
}
