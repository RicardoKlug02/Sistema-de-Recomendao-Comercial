export default function Seletor({ rotulo, todos, opcoes = [], valor, aoMudar, ...propriedades }) {
  const lista = Array.isArray(opcoes) ? opcoes : Object.entries(opcoes).map(([id, nome]) => ({ id, nome }))
  return (
    <label>
      {rotulo}
      <select aria-label={rotulo} value={valor} onChange={(e) => aoMudar(e.target.value)} {...propriedades}>
        {todos !== undefined && <option value="">{todos}</option>}
        {lista.map((o) => <option key={o.id} value={o.id}>{o.nome}</option>)}
      </select>
    </label>
  )
}
