export default function EstadoConsulta({ carregando, erro, aoTentar }) {
  if (carregando)
    return (
      <p className="estado-consulta" role="status">
        Carregando dados… O servidor pode levar alguns instantes para iniciar.
      </p>
    )
  if (erro)
    return (
      <div className="estado-consulta estado-erro" role="alert">
        <p>{erro}</p>
        <button className="botao-secundario" onClick={aoTentar}>
          Tentar novamente
        </button>
      </div>
    )
  return null
}
