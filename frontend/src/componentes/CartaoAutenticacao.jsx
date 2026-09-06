export default function CartaoAutenticacao({ titulo, subtitulo, referenciaTitulo, children }) {
  return (
    <section className="cartao-autenticacao" aria-labelledby="titulo-autenticacao">
      <header className="cabecalho-autenticacao">
        <h1 id="titulo-autenticacao" ref={referenciaTitulo} tabIndex={-1}>{titulo}</h1>
        <p>{subtitulo}</p>
      </header>
      {children}
    </section>
  )
}
