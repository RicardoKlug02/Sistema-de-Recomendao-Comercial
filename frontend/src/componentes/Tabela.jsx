export default function Tabela({ colunas, children }) {
  return (
    <div className="rolagem-tabela">
      <table>
        <thead>
          <tr>
            {colunas.map((coluna) => (
              <th key={coluna}>{coluna}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}
