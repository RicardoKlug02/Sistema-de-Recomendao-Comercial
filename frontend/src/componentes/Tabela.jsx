export default function Tabela({ colunas, className, rotulo, children }) {
  return (
    <div className="rolagem-tabela">
      <table className={className} aria-label={rotulo}>
        <thead><tr>{colunas.map((coluna, indice) => <th key={indice}>{coluna}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}
