// Compartilha a seleção exclusiva por tipo de oportunidade ou situação do cliente.
export default function FiltrosTipo({ rotulo, opcoes, selecionada, aoSelecionar, contar }) {
  return (
    <div className="filtros-tipo" role="group" aria-label={rotulo}>
      {opcoes.map((opcao) => (
        <button key={opcao} aria-pressed={selecionada === opcao} onClick={() => aoSelecionar(opcao)}>
          {opcao}
          <span>{contar(opcao)}</span>
        </button>
      ))}
    </div>
  )
}
