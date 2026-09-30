import { useId } from 'react'

// Estrutura única para cards de indicadores, gráficos, listas e formulários.
export default function Cartao({
  titulo,
  descricao,
  id,
  className = '',
  acao,
  children,
}) {
  const identificadorTitulo = useId()
  return (
    <section
      id={id}
      className={`cartao ${className}`}
      aria-labelledby={identificadorTitulo}
      tabIndex={id ? -1 : undefined}
    >
      <header className="cabecalho-cartao">
        <div>
          <h2 id={identificadorTitulo}>{titulo}</h2>
          {descricao && <p>{descricao}</p>}
        </div>
        {acao}
      </header>
      {children}
    </section>
  )
}
