import Icone from './Icone'

// Estados explícitos evitam apresentar ausência de dados como resultado financeiro zero.
export default function EstadoConsulta({
  carregando,
  erro,
  vazio,
  mensagem = 'Nenhum resultado encontrado.',
  aoTentar,
}) {
  if (erro)
    return (
      <div className="estado-consulta estado-erro" role="alert">
        <Icone nome="alertas" />
        <div>
          <strong>Não foi possível carregar</strong>
          <p>{erro}</p>
          {aoTentar && (
            <button className="botao-secundario" onClick={aoTentar}>
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    )
  if (carregando)
    return (
      <div className="estado-consulta" role="status">
        <span className="carregador" />
        <span>Carregando informações…</span>
      </div>
    )
  if (vazio)
    return (
      <div className="estado-consulta estado-vazio">
        <Icone nome="busca" />
        <p>{mensagem}</p>
      </div>
    )
  return null
}
