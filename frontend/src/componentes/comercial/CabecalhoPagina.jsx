export default function CabecalhoPagina({
  titulo,
  descricao,
  categoria = 'INTELIGÊNCIA COMERCIAL',
  children,
  referencia,
}) {
  return (
    <header className="cabecalho-painel">
      <div>
        <p className="sobretitulo">{categoria}</p>
        <h1 ref={referencia} tabIndex={-1}>
          {titulo}
        </h1>
        {descricao && <p>{descricao}</p>}
      </div>
      {children && <div className="acoes-cabecalho">{children}</div>}
    </header>
  )
}
