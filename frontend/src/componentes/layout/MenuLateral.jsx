import Marca from '../Marca'
import Icone from '../Icone'
import { secoes } from '../../secoes'

const perfis = { admin: 'Administrador', gestor: 'Gestor', vendedor: 'Representante' }

export default function MenuLateral({ usuario, gestor, secaoAtiva, aoNavegar, aoSair }) {
  const inicio = gestor ? 'painel' : 'alertas'
  const principais = (gestor ? ['painel', 'clientes', 'alertas'] : ['alertas', 'clientes'])
    .map(id => secoes.find(s => s.id === id))
  const outros = secoes.filter(s => !principais.includes(s) && (gestor || !s.restrita))
  const link = ({ id, titulo }) => (
    <a key={id} href={`#${id}`} aria-current={secaoAtiva === id ? 'page' : undefined}
      onClick={e => { e.preventDefault(); aoNavegar(id); e.currentTarget.closest('details')?.removeAttribute('open') }}>
      <Icone nome={id} tamanho={19} />{id === 'alertas' && !gestor ? 'Hoje' : titulo}
    </a>
  )
  return (
    <aside className="menu-lateral">
      <a className="marca" href={`#${inicio}`} onClick={(e) => { e.preventDefault(); aoNavegar(inicio) }}><Marca /></a>
      <p className="legenda-menu">MENU</p>
      <nav aria-label="Menu principal">
        {principais.map(link)}
        <details className="menu-outras-secoes">
          <summary>Mais</summary>
          <div>{outros.map(link)}</div>
        </details>
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
