<<<<<<< Updated upstream
import { useState } from 'react'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import FiltrosCarteira from '../componentes/comercial/FiltrosCarteira'
import CartaoCliente from '../componentes/comercial/CartaoCliente'
import EstadoVazio from '../componentes/comercial/EstadoVazio'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import { adaptarCliente } from '../servicos/dadosComerciais'
import useConsulta from '../ganchos/useConsulta'

export default function Clientes({ versao, aoAtualizar, aoAbrirCliente }) {
  const [busca, definirBusca] = useState('')
  const [ordem, definirOrdem] = useState('nome')
  const termo = busca.trim()
  const consulta = useConsulta(
    termo.length >= 2 ? `/clientes/busca?termo=${encodeURIComponent(termo)}` : null,
    versao,
  )
  const formatoInvalido = consulta.dados !== null && !Array.isArray(consulta.dados)
  const clientes = (Array.isArray(consulta.dados) ? consulta.dados.map(adaptarCliente) : []).sort(
    (a, b) =>
      (ordem === 'cidade' ? (a.cidade || '').localeCompare(b.cidade || '', 'pt-BR') : 0) ||
      a.nome.localeCompare(b.nome, 'pt-BR'),
  )
  return (
    <main className="conteudo-painel">
      <CabecalhoPagina
        titulo="Cada cliente, uma relação."
        descricao="Busque na sua base e abra o perfil para conhecer o histórico de compras."
        identificador="titulo-clientes"
      />
      <FiltrosCarteira
        busca={busca}
        aoBuscar={definirBusca}
        rotulo="Buscar cliente"
        dica="Razão social, nome fantasia ou CNPJ/CPF"
        campos={[
          {
            nome: 'ordem',
            titulo: 'Ordenar resultados',
            valor: ordem,
            aoAlterar: definirOrdem,
            opcoes: [
              { valor: 'nome', rotulo: 'Nome do cliente' },
              { valor: 'cidade', rotulo: 'Cidade' },
            ],
          },
        ]}
      />
      <p className="contagem-resultados contagem-busca" role="status">
        {termo.length < 2
          ? 'Digite pelo menos dois caracteres para consultar a base.'
          : consulta.carregando
            ? 'Buscando clientes…'
            : consulta.erro || formatoInvalido
              ? 'Busca não concluída.'
              : `${clientes.length} resultados retornados para esta busca.`}
      </p>
      <EstadoConsulta
        {...consulta}
        erro={
          consulta.erro ||
          (formatoInvalido ? 'Não foi possível interpretar os clientes retornados pelo servidor.' : '')
        }
        aoTentar={aoAtualizar}
      />
      {termo.length < 2 ? (
        <EstadoVazio
          titulo="Encontre seu próximo contato"
          descricao="Pesquise pelo nome ou documento do cliente. A consulta retorna os resultados encontrados, não uma listagem completa da carteira."
        />
      ) : (
        !consulta.carregando &&
        !consulta.erro &&
        !formatoInvalido &&
        (clientes.length ? (
          <div className="grade-clientes">
            {clientes.map((cliente) => (
              <CartaoCliente key={cliente.id} cliente={cliente} aoAbrirCliente={aoAbrirCliente} />
            ))}
          </div>
        ) : (
          <EstadoVazio
            titulo="Nenhum cliente encontrado"
            descricao="Tente outro trecho do nome ou o CNPJ/CPF completo."
          />
        ))
      )}
      <p className="nota-painel">
        A busca retorna um conjunto limitado de resultados. Refine o nome ou informe o documento completo para
        localizar um cliente específico.
      </p>
    </main>
  )
=======
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
export function Clientes() {
  const [termo, definirTermo] = useState("");
  const [busca, buscar] = useState("");
  const [pagina, paginar] = useState(1);
  return (
    <Cartao
      titulo="Carteira de clientes"
      descricao="Consulte o histórico e prepare sua próxima visita."
    >
      <form
        className="filtros"
        onSubmit={(e) => {
          e.preventDefault();
          buscar(termo);
          paginar(1);
        }}
      >
        <Campo
          rotulo="Buscar cliente"
          placeholder="Nome, documento ou cidade"
          value={termo}
          onChange={(e) => definirTermo(e.target.value)}
        />
        <button className="botao-principal">Buscar</button>
      </form>
      <Consulta
        caminho={`/clientes?pagina=${pagina}&termo=${encodeURIComponent(busca)}`}
      >
        {({ itens, total }) => (
          <>
            <Tabela
              colunas={["Cliente", "Cidade / UF", "Grupo econômico", "Ação"]}
              linhas={itens.map((c) => [
                <a href={`#/clientes/${c.id}`}>{c.razao_social}</a>,
                [c.cidade, c.estado].filter(Boolean).join(" / "),
                c.grupo_economico,
                <a className="botao-detalhes" href={`#/clientes/${c.id}`}>
                  Abrir ficha →
                </a>,
              ])}
            />
            <Paginacao pagina={pagina} total={total} aoMudar={paginar} />
          </>
        )}
      </Consulta>
    </Cartao>
  );
}
export function FichaCliente({ id }) {
  const [aba, selecionar] = useState("resumo");
  const [pagina, paginar] = useState(1);
  return (
    <>
      <a className="voltar" href="#/clientes">
        ← Voltar para clientes
      </a>
      <Consulta caminho={`/clientes/${id}`}>
        {(c) => (
          <>
            <section className="hero-cliente">
              <div>
                <p className="sobretitulo">FICHA DO CLIENTE</p>
                <h2>{c.razao_social}</h2>
                <p>
                  {c.cnpj_cpf || "Documento não informado"} ·{" "}
                  {[c.cidade, c.estado].filter(Boolean).join(" / ") ||
                    "Localização não informada"}
                </p>
              </div>
              <Etiqueta>{c.grupo_economico || "Sem grupo econômico"}</Etiqueta>
            </section>
            <div className="abas" role="group" aria-label="Seções da ficha">
              {[
                ["resumo", "Visão geral"],
                ["historico", "Histórico de compras"],
                ["recomendacoes", "Recomendações"],
              ].map(([valor, titulo]) => (
                <button
                  key={valor}
                  className={aba === valor ? "ativa" : ""}
                  aria-pressed={aba === valor}
                  onClick={() => selecionar(valor)}
                >
                  {titulo}
                </button>
              ))}
            </div>
            {c.mensagem && <p className="aviso">{c.mensagem}</p>}
            {aba === "resumo" && (
              <>
                <div className="grade-indicadores">
                  <CartaoIndicador
                    titulo="Faturamento recente"
                    valor={moeda(c.performance_yoy?.faturamento_recente)}
                    detalhe={
                      c.performance_yoy?.periodo_recente || "Sem histórico"
                    }
                  />
                  <CartaoIndicador
                    titulo="Variação anual"
                    valor={
                      c.performance_yoy?.crescimento_pct == null
                        ? "Sem base"
                        : `${c.performance_yoy.crescimento_pct}%`
                    }
                    detalhe="Mesmo mês do ano anterior"
                  />
                  <CartaoIndicador
                    titulo="Reposições"
                    valor={String(c.sugestoes_reposicao.length)}
                    detalhe="Produtos na janela de compra"
                  />
                  <CartaoIndicador
                    titulo="Produtos em abandono"
                    valor={String(c.produtos_em_abandono.length)}
                    detalhe="Revisar na próxima visita"
                  />
                </div>
                <Cartao titulo="Relacionamento por fábrica">
                  <Tabela
                    colunas={[
                      "Fábrica",
                      "Última compra",
                      "Ciclo médio",
                      "Dias sem comprar",
                      "Situação",
                    ]}
                    linhas={c.resumo_fabricas.map((f) => [
                      f.fabrica,
                      f.ultima_compra,
                      `${f.ciclo_medio_dias} dias`,
                      f.dias_sem_comprar,
                      <Etiqueta>{f.status}</Etiqueta>,
                    ])}
                  />
                </Cartao>
                <Cartao titulo="Produtos em abandono">
                  <Tabela
                    colunas={[
                      "Produto",
                      "SKU",
                      "Dias sem comprar",
                      "Ciclo habitual",
                    ]}
                    linhas={c.produtos_em_abandono.map((p) => [
                      p.nome,
                      p.sku,
                      p.dias_parado,
                      `${p.ciclo_habitual} dias`,
                    ])}
                    vazio="Nenhum produto em abandono identificado."
                  />
                </Cartao>
              </>
            )}
            {aba === "historico" && (
              <Cartao titulo="Pedidos e itens comprados">
                <Consulta caminho={`/clientes/${id}/vendas?pagina=${pagina}`}>
                  {({ itens, total }) => (
                    <>
                      <Tabela
                        colunas={[
                          "Pedido",
                          "Data",
                          "Fábrica",
                          "Valor",
                          "Itens",
                        ]}
                        linhas={itens.map((v) => [
                          v.numero_pedido,
                          data(v.data_venda),
                          v.fabrica,
                          moeda(v.valor_total),
                          <details>
                            <summary>{v.itens.length} produtos</summary>
                            <ul>
                              {v.itens.map((i) => (
                                <li key={i.id}>
                                  {i.nome} · {i.quantidade} ×{" "}
                                  {moeda(i.preco_unitario)} · Subtotal{" "}
                                  {moeda(i.subtotal)}
                                </li>
                              ))}
                            </ul>
                          </details>,
                        ])}
                      />
                      <Paginacao
                        pagina={pagina}
                        total={total}
                        aoMudar={paginar}
                      />
                    </>
                  )}
                </Consulta>
              </Cartao>
            )}
            {aba === "recomendacoes" && (
              <>
                <Cartao
                  titulo="Reposição sugerida"
                  descricao="Estimativa baseada no intervalo entre compras."
                >
                  <Tabela
                    colunas={[
                      "Produto",
                      "Ciclo",
                      "Última compra há",
                      "Volume habitual",
                      "Situação",
                    ]}
                    linhas={c.sugestoes_reposicao.map((p) => [
                      p.nome,
                      `${p.ciclo_medio} dias`,
                      `${p.dias_desde_ultima} dias`,
                      p.volume_habitual,
                      <Etiqueta>{p.status}</Etiqueta>,
                    ])}
                  />
                </Cartao>
                <Cartao
                  titulo="Expansão de mix"
                  descricao="Produtos consumidos por grupos com histórico semelhante."
                >
                  <div className="grade-resumos">
                    {c.sugestoes_expansao_mix.map((p) => (
                      <article className="sugestao" key={p.produto_id}>
                        <Etiqueta>{p.classificacao}</Etiqueta>
                        <h3>{p.nome}</h3>
                        <p>
                          SKU {p.sku} · Afinidade {p.afinidade_percentual}%
                        </p>
                        <p>{p.motivo}</p>
                      </article>
                    ))}
                  </div>
                  {!c.sugestoes_expansao_mix.length && (
                    <p className="estado-vazio">
                      Histórico insuficiente para sugerir novos produtos.
                    </p>
                  )}
                </Cartao>
              </>
            )}
          </>
        )}
      </Consulta>
    </>
  );
>>>>>>> Stashed changes
}
