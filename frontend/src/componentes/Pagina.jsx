import { useEffect, useRef } from 'react'

export default function Pagina({ titulo, descricao, acoes, className = '', children }) {
  const referencia = useRef(null)
  useEffect(() => { referencia.current.focus() }, [])
  return (
    <main className={`conteudo-painel ${className}`.trim()}>
      <header className="cabecalho-painel">
        <div>
          <p className="sobretitulo">INTELIGÊNCIA COMERCIAL</p>
          <h1 id="titulo-pagina" ref={referencia} tabIndex={-1}>{titulo}</h1>
          {descricao && <p>{descricao}</p>}
        </div>
        {acoes && <div className="acoes-cabecalho">{acoes}</div>}
      </header>
      {children}
    </main>
  )
}
