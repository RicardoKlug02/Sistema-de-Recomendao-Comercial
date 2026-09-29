export default function CabecalhoPagina({ titulo, descricao, identificador }) {
  return (
    <header className="cabecalho-painel">
      <div>
        <p className="sobretitulo">INTELIGÊNCIA COMERCIAL</p>
        <h1 id={identificador} tabIndex={-1}>
          {titulo}
        </h1>
        <p>{descricao}</p>
      </div>
      <span className="aviso-dados">
        <span aria-hidden="true">●</span> Dados importados
      </span>
    </header>
  )
}
