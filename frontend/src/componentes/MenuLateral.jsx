import Marca from './Marca'
import Icone from './Icone'
import { secoes } from '../secoes'
import { ehGestor } from '../servicos/autenticacao'

const perfis = {
  admin: 'Administrador',
  gestor: 'Gestor',
  vendedor: 'Representante',
}

export default function MenuLateral({ usuario, secaoAtiva, aoNavegar, aoSair }) {
  const gestor = ehGestor(usuario)
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
      <p className="legenda-menu">MENU</p>
      <nav aria-label="Menu principal">
        {secoes
          .filter((s) => gestor || !s.restrita)
          .map(({ id, titulo }) => (
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
            </a>
          ))}
      </nav>
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
