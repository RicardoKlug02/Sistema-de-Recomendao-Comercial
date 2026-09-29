import { useState } from "react";
import useConsulta from "../hooks/useConsulta";
export function Consulta({ caminho, children, versao = 0 }) {
  const [tentativa, tentar] = useState(0);
  return (
    <Resultado
      key={`${caminho}:${versao}:${tentativa}`}
      caminho={caminho}
      tentar={() => tentar(tentativa + 1)}
    >
      {children}
    </Resultado>
  );
}
function Resultado({ caminho, tentar, children }) {
  const { dados, erro, carregando } = useConsulta(caminho);
  if (carregando)
    return (
      <div className="estado-vazio" role="status">
        Carregando informações…
      </div>
    );
  if (erro)
    return (
      <div className="estado-vazio" role="alert">
        <p>{erro}</p>
        <button className="botao-secundario" onClick={tentar}>
          Tentar novamente
        </button>
      </div>
    );
  return children(dados);
}
export function Tabela({
  colunas,
  linhas,
  vazio = "Nenhum registro encontrado.",
}) {
  if (!linhas.length) return <div className="estado-vazio">{vazio}</div>;
  return (
    <div
      className="rolagem-tabela"
      tabIndex={0}
      role="region"
      aria-label="Resultados"
    >
      <table>
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j}>{c ?? "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Etiqueta({ children }) {
  return <span className="etiqueta">{children}</span>;
}
export function Paginacao({ pagina, total, tamanho = 20, aoMudar }) {
  return (
    <nav className="paginacao-importacao" aria-label="Paginação">
      <span>
        {total} registros · Página {pagina} de{" "}
        {Math.max(1, Math.ceil(total / tamanho))}
      </span>
      <div>
        <button
          className="botao-secundario"
          disabled={pagina <= 1}
          onClick={() => aoMudar(pagina - 1)}
        >
          Anterior
        </button>
        <button
          className="botao-secundario"
          disabled={pagina * tamanho >= total}
          onClick={() => aoMudar(pagina + 1)}
        >
          Próxima
        </button>
      </div>
    </nav>
  );
}
export function Campo({ rotulo, ...props }) {
  return (
    <label className="campo">
      <span>{rotulo}</span>
      <input {...props} />
    </label>
  );
}
