import { moeda, data } from "../servicos/formatacao";
import { useState } from "react";
import Cartao from "../componentes/Cartao";
import CartaoIndicador from "../componentes/CartaoIndicador";
import {
  Campo,
  Consulta,
  Tabela,
  Paginacao,
  Etiqueta,
} from "../componentes/Elementos";
import { api } from "../servicos/api";
export function Painel() {
  return (
    <Consulta caminho="/comercial/resumo">
      {(r) => (
        <>
          <div className="grade-indicadores">
            {[
              ["Faturamento", moeda(r.faturamento), "Histórico importado"],
              ["Clientes", r.clientes, "Carteira cadastrada"],
              ["Pedidos", r.pedidos, "Pedidos importados"],
              ["Fábricas", r.fabricas, "Parceiros comerciais"],
            ].map(([titulo, valor, detalhe]) => (
              <CartaoIndicador
                key={titulo}
                titulo={titulo}
                valor={String(valor)}
                detalhe={detalhe}
              />
            ))}
          </div>
          <div className="grade-resumos">
            <Cartao
              titulo="Faturamento mensal"
              descricao="Últimos 12 meses com vendas"
            >
              <div className="grafico-colunas">
                {r.mensal.map((m) => (
                  <div
                    key={m.mes}
                    className="coluna-mensal"
                    tabIndex={0}
                    aria-label={`${m.mes}: ${moeda(m.valor)}`}
                  >
                    <span className="valor-coluna">{moeda(m.valor)}</span>
                    <div className="trilho-coluna">
                      <span
                        style={{
                          height: `${(m.valor / Math.max(1, ...r.mensal.map((i) => i.valor))) * 100}%`,
                        }}
                      />
                    </div>
                    <span>{m.mes}</span>
                  </div>
                ))}
              </div>
              {!r.mensal.length && (
                <p className="estado-vazio">
                  Importe pedidos para visualizar o faturamento.
                </p>
              )}
            </Cartao>
            <Cartao titulo="Principais clientes">
              <ol className="lista-clientes">
                {r.top_clientes.map((c) => (
                  <li key={c.id}>
                    <a href={`#/clientes/${c.id}`}>{c.nome}</a>
                    <strong>{moeda(c.valor)}</strong>
                  </li>
                ))}
              </ol>
              {!r.top_clientes.length && (
                <p className="estado-vazio">Nenhuma venda disponível.</p>
              )}
            </Cartao>
          </div>
          <Cartao
            titulo="Prepare sua próxima visita"
            descricao="Encontre oportunidades no histórico de cada cliente."
          >
            <div className="acoes">
              <a className="botao-secundario" href="#/clientes">
                Consultar clientes →
              </a>
              <a className="botao-secundario" href="#/alertas">
                Ver alertas de recompra →
              </a>
              <a className="botao-secundario" href="#/relatorios">
                Analisar vendas →
              </a>
            </div>
          </Cartao>
        </>
      )}
    </Consulta>
  );
}
export function Alertas() {
  const [filtro, filtrar] = useState("todos");
  return (
    <Cartao
      titulo="Acompanhamento de recompra"
      descricao="Alertas calculados a partir do histórico disponível. Não representam mensagens enviadas."
    >
      <label className="campo">
        Situação
        <select value={filtro} onChange={(e) => filtrar(e.target.value)}>
          <option value="todos">Todos os alertas</option>
          <option value="critico">Risco crítico</option>
        </select>
      </label>
      <Consulta caminho="/clientes/alertas/home?limite=50">
        {(lista) => (
          <Tabela
            colunas={[
              "Cliente",
              "Produto",
              "Atraso",
              "Volume médio",
              "Situação",
              "Ação",
            ]}
            linhas={lista
              .filter((a) => filtro === "todos" || a.status.includes("Crítico"))
              .map((a) => [
                a.razao_social,
                a.nome_produto,
                `${a.dias_atraso} dias`,
                a.volume_medio_pedido,
                <Etiqueta>{a.status}</Etiqueta>,
                <a href={`#/clientes/${a.cliente_id}`}>Consultar cliente →</a>,
              ])}
            vazio="Nenhum alerta identificado com o histórico atual."
          />
        )}
      </Consulta>
    </Cartao>
  );
}
export function Oportunidades() {
  const [selecionados, selecionar] = useState([]);
  const [sugestoes, definir] = useState(null);
  const [erro, falhar] = useState("");
  const [ocupado, ocupar] = useState(false);
  const [termo, filtrar] = useState("");
  async function recomendar(e) {
    e.preventDefault();
    ocupar(true);
    falhar("");
    try {
      definir(
        await api("/clientes/cross-selling", {
          method: "POST",
          body: selecionados.map((p) => p.id),
        }),
      );
    } catch (e) {
      falhar(e.message);
    } finally {
      ocupar(false);
    }
  }
  return (
    <>
      <Cartao
        titulo="Produtos que combinam"
        descricao="Selecione os produtos de interesse para descobrir sugestões complementares."
      >
        <form onSubmit={recomendar}>
          <Campo
            rotulo="Buscar produto"
            value={termo}
            onChange={(e) => filtrar(e.target.value)}
            placeholder="Nome ou SKU"
          />
          <Consulta
            caminho={`/comercial/produtos?termo=${encodeURIComponent(termo)}`}
          >
            {(produtos) => (
              <div className="selecao-produtos">
                {produtos.map((p) => (
                  <label key={p.id}>
                    <input
                      type="checkbox"
                      checked={selecionados.some((s) => s.id === p.id)}
                      onChange={(e) => {
                        selecionar(
                          e.target.checked
                            ? [...selecionados, p]
                            : selecionados.filter((s) => s.id !== p.id),
                        );
                        definir(null);
                      }}
                    />
                    {p.nome} <small>{p.sku}</small>
                  </label>
                ))}
                {!produtos.length && <p>Nenhum produto encontrado.</p>}
              </div>
            )}
          </Consulta>
          <p>
            {selecionados.length} selecionados{" "}
            {selecionados.map((p) => (
              <button
                type="button"
                className="chip"
                key={p.id}
                onClick={() => {
                  selecionar(selecionados.filter((s) => s.id !== p.id));
                  definir(null);
                }}
              >
                {p.nome} ×
              </button>
            ))}
          </p>
          <button
            className="botao-principal"
            disabled={!selecionados.length || ocupado}
          >
            {ocupado ? "Analisando…" : "Buscar sugestões"}
          </button>
        </form>
        {erro && (
          <p role="alert" className="erro-campo">
            {erro}
          </p>
        )}
      </Cartao>
      {sugestoes && (
        <Cartao titulo="Sugestões de venda complementar">
          <Tabela
            colunas={["Produto", "SKU", "Confiança", "Motivo"]}
            linhas={sugestoes.map((p) => [
              p.nome,
              p.sku,
              `${p.confianca_pct}%`,
              p.motivo,
            ])}
            vazio="Não há evidências suficientes para sugerir produtos para esta seleção."
          />
        </Cartao>
      )}
      <Cartao
        titulo="Oportunidades por cliente"
        descricao="Consulte reposições, produtos em abandono e expansão de mix na ficha individual."
      >
        <a href="#/clientes">Abrir carteira de clientes →</a>
      </Cartao>
    </>
  );
}
export function Relatorios() {
  const [filtros, definir] = useState({
    inicio: "",
    fim: "",
    cliente: "",
    categoria: "",
    regiao: "",
    fabrica: "",
  });
  const [consulta, consultar] = useState("");
  const [pagina, paginar] = useState(1);
  return (
    <Cartao
      titulo="Desempenho comercial"
      descricao="Filtre pedidos e exporte o resultado consolidado."
    >
      <form
        className="filtros"
        onSubmit={(e) => {
          e.preventDefault();
          consultar(new URLSearchParams(filtros).toString());
          paginar(1);
        }}
      >
        {[
          ["inicio", "Data inicial", "date"],
          ["fim", "Data final", "date"],
          ["cliente", "Cliente", "search"],
          ["categoria", "Categoria", "search"],
          ["regiao", "Cidade / região", "search"],
          ["fabrica", "Fábrica", "search"],
        ].map(([chave, rotulo, tipo]) => (
          <Campo
            key={chave}
            rotulo={rotulo}
            type={tipo}
            value={filtros[chave]}
            min={chave === "fim" ? filtros.inicio : undefined}
            onChange={(e) => definir({ ...filtros, [chave]: e.target.value })}
          />
        ))}
        <button className="botao-principal">Aplicar filtros</button>
      </form>
      <Consulta caminho={`/comercial/relatorio?${consulta}&pagina=${pagina}`}>
        {(r) => (
          <>
            <div className="grade-indicadores">
              <CartaoIndicador
                titulo="Total filtrado"
                valor={moeda(r.valor_total)}
                detalhe="Soma das linhas selecionadas"
              />
              <CartaoIndicador
                titulo="Pedidos"
                valor={String(r.total)}
                detalhe="Pedidos encontrados"
              />
            </div>
            <button className="botao-secundario" onClick={() => window.print()}>
              Imprimir / salvar PDF
            </button>
            <Tabela
              colunas={["Pedido", "Data", "Cliente", "Fábrica", "Valor"]}
              linhas={r.itens.map((v) => [
                v.numero_pedido,
                data(v.data_venda),
                <a href={`#/clientes/${v.cliente_id}`}>{v.cliente}</a>,
                v.fabrica,
                moeda(v.valor_total),
              ])}
            />
            <Paginacao pagina={pagina} total={r.total} aoMudar={paginar} />
            <p className="nota-painel">
              A impressão contém a página atual. O total considera todos os
              resultados filtrados.
            </p>
          </>
        )}
      </Consulta>
    </Cartao>
  );
}
