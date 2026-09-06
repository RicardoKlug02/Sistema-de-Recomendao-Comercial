import { useId } from 'react'

// Agrupa conteúdo do painel com título acessível e aparência compartilhada.
export default function Cartao({ titulo, descricao, id, className = '', children }) {
  const identificadorTitulo = useId()
  return (
    <section id={id} className={`cartao ${className}`} aria-labelledby={identificadorTitulo} tabIndex={id ? -1 : undefined}>
      <header className="cabecalho-cartao">
        <h2 id={identificadorTitulo}>{titulo}</h2>
        {descricao && <p>{descricao}</p>}
      </header>
      {children}
    </section>
  )
}
