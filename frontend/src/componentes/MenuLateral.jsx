<<<<<<< Updated upstream
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
=======
const itens = [
  ["painel", "Visão geral", "◫"],
  ["clientes", "Clientes", "◎"],
  ["oportunidades", "Oportunidades", "↗"],
  ["alertas", "Alertas", "◷"],
  ["relatorios", "Relatórios", "▤"],
  ["importacoes", "Importação", "↓"],
  ["usuarios", "Usuários", "♙"],
  ["perfil", "Minha conta", "○"],
];
export default function MenuLateral({ usuario, secaoAtiva, aoSair }) {
  const admin = ["admin", "gestor"].includes(usuario.perfil);
  return (
    <aside className="menu-lateral">
      <a className="marca" href="#/painel">
        <span className="simbolo-marca">▥</span>
        <span>
          Rio Verde<small>REPRESENTAÇÕES</small>
        </span>
      </a>
      <p className="legenda-menu">INTELIGÊNCIA COMERCIAL</p>
      <nav aria-label="Menu principal">
        {itens
          .filter(([id]) => !["usuarios", "importacoes"].includes(id) || admin)
          .map(([id, titulo, icone]) => (
            <a
              key={id}
              href={`#/${id}`}
              aria-current={secaoAtiva === id ? "page" : undefined}
            >
              <span aria-hidden="true">{icone}</span>
              {titulo}
            </a>
          ))}
      </nav>
      <div className="rodape-menu">
        <div className="perfil">
          <span className="avatar">
            {usuario.nome.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong>{usuario.nome}</strong>
            <small>{usuario.perfil}</small>
          </div>
        </div>
        <button className="botao-sair" onClick={aoSair}>
          Sair da conta <span>↗</span>
>>>>>>> Stashed changes
        </button>
      </div>
    </aside>
  );
}
