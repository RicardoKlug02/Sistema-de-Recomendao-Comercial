export default function Seletor({ rotulo, todos, opcoes = [], valor, aoMudar, disabled = false }) {
  return (
    <label>
      {rotulo}
      <select aria-label={rotulo} value={valor} disabled={disabled} onChange={(e) => aoMudar(e.target.value)}>
        <option value="">{todos}</option>
        {opcoes.map((o) => (
          <option key={o.id} value={o.id}>
            {o.nome}
          </option>
        ))}
      </select>
    </label>
  )
}
