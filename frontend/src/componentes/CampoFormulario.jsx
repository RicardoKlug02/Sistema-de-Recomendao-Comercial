export default function CampoFormulario({ id, rotulo, erro, ...propriedadesCampo }) {
  return (
    <div className="campo-formulario">
      <label htmlFor={id}>{rotulo}</label>
      <input id={id} name={id} required aria-invalid={Boolean(erro)}
        aria-describedby={erro ? `${id}-erro` : undefined} {...propriedadesCampo} />
      {erro && <p className="erro-campo" id={`${id}-erro`}>{erro}</p>}
    </div>
  )
}
