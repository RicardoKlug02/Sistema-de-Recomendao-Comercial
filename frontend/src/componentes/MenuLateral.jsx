const itensMenu = [
  { destino: 'painel', titulo: 'Dashboard', desenho: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z' },
  { destino: 'clientes', titulo: 'Clientes', desenho: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75' },
  { destino: 'importacoes', titulo: 'Importação', desenho: 'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5' },
]

// Navega entre o painel, o resumo de clientes e a importação.
export default function MenuLateral({ usuario, secaoAtiva, aoNavegar, aoSair }) {
  return (
    <aside className="menu-lateral">
      <a className="marca" href="#painel" onClick={(evento) => { evento.preventDefault(); aoNavegar('painel') }}>
        <span className="simbolo-marca" aria-hidden="true">▥</span>
        <span>Rio Verde <small>REPRESENTAÇÕES</small></span>
      </a>
      <p className="legenda-menu">COMERCIAL</p>
      <nav aria-label="Menu principal">
        {itensMenu.map(({ destino, titulo, desenho }) => (
          <a key={destino} href={`#${destino}`} aria-current={secaoAtiva === destino ? 'location' : undefined}
            onClick={(evento) => { evento.preventDefault(); aoNavegar(destino) }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={desenho} /></svg>
            {titulo}
          </a>
        ))}
      </nav>
      <div className="rodape-menu">
        <div className="perfil"><span className="avatar" aria-hidden="true">{usuario.email.slice(0, 2).toUpperCase()}</span><div><strong>{usuario.email}</strong><small>Representante</small></div></div>
        <button className="botao-sair" onClick={aoSair}>Sair da conta <span aria-hidden="true">↗</span></button>
      </div>
    </aside>
  )
}
