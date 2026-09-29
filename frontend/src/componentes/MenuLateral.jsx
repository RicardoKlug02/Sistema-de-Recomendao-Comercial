import Marca from './comercial/Marca'
import Icone from './comercial/Icone'

const itensMenu = [
  { destino: 'painel', titulo: 'Visão geral' },
  { destino: 'clientes', titulo: 'Clientes' },
  { destino: 'importacoes', titulo: 'Importação' },
]

// Centraliza a navegação entre telas e o encerramento da sessão.
export default function MenuLateral({ usuario, secaoAtiva, aoNavegar, aoSair }) {
  return (
    <aside className="menu-lateral">
      <a
        className="marca"
        href="#painel"
        onClick={(evento) => {
          evento.preventDefault()
          aoNavegar('painel')
        }}
      >
        <Marca />
      </a>
      <p className="legenda-menu">ESPAÇO COMERCIAL</p>
      <nav aria-label="Menu principal">
        {itensMenu.map(({ destino, titulo }) => (
          <a
            key={destino}
            href={`#${destino}`}
            aria-current={secaoAtiva === destino ? 'page' : undefined}
            onClick={(evento) => {
              evento.preventDefault()
              aoNavegar(destino)
            }}
          >
            <Icone nome={destino} />
            {titulo}
            {secaoAtiva === destino && <span className="ponto-menu" aria-hidden="true" />}
          </a>
        ))}
      </nav>
      <div className="rodape-menu">
        <div className="perfil">
          <span className="avatar" aria-hidden="true">
            {usuario.email.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong>{usuario.nome || usuario.email}</strong>
            <small>
              {usuario.perfil === 'admin'
                ? 'Administrador'
                : usuario.perfil === 'gestor'
                  ? 'Gestor'
                  : 'Representante comercial'}
            </small>
          </div>
        </div>
        <button className="botao-sair" onClick={aoSair}>
          Sair da conta <Icone nome="sair" tamanho={17} />
        </button>
      </div>
    </aside>
  )
}
