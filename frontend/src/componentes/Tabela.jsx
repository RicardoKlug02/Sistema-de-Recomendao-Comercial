export default function Tabela({ colunas, className, children }) {
  return (
    <div className="rolagem-tabela">
      <table className={className}>
        <thead><tr>{colunas.map((coluna, indice) => <th key={indice}>{coluna}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}
