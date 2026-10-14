export default function FiltroFabrica({ fabricas = [], valor, aoMudar, disabled = false }) {
  return <label>Fábrica<select aria-label="Fábrica" value={valor} disabled={disabled} onChange={(e) => aoMudar(e.target.value)}>
    <option value="">Todas as fábricas</option>
    {fabricas.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}
  </select></label>
}
