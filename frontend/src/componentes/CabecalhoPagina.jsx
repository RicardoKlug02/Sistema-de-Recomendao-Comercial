import { useEffect, useRef } from 'react'

export default function CabecalhoPagina({ titulo, descricao, children }) {
  const referencia = useRef(null)
  useEffect(() => {
    referencia.current.focus()
  }, [])
  return (
    <header className="cabecalho-painel">
      <div>
        <p className="sobretitulo">INTELIGÊNCIA COMERCIAL</p>
        <h1 id="titulo-pagina" ref={referencia} tabIndex={-1}>
          {titulo}
        </h1>
        {descricao && <p>{descricao}</p>}
      </div>
      {children && <div className="acoes-cabecalho">{children}</div>}
    </header>
  )
}
