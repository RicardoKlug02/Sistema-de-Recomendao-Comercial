import { useState } from 'react'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import CartaoCliente from '../componentes/comercial/CartaoCliente'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import Paginacao from '../componentes/comercial/Paginacao'
import Icone from '../componentes/comercial/Icone'
import Cartao from '../componentes/Cartao'
import RitmoCompras from '../componentes/RitmoCompras'
import CartaoIndicador from '../componentes/CartaoIndicador'
import useDados from '../servicos/useDados'
import FiltroFabrica from '../componentes/comercial/FiltroFabrica'
import { formatarMoeda } from '../servicos/dadosPainel'

export default function Clientes({ inicial = null, fabricas = [] }) {
  const [fabrica, definirFabrica] = useState('')
  const [busca, definirBusca] = useState('')
  const [termo, definirTermo] = useState('')
  const [pagina, definirPagina] = useState(1)
  const [clienteId, definirCliente] = useState(inicial)
  const [rede, definirRede] = useState(true)
  const lista = useDados(
    clienteId
      ? null
      : `/comercial/clientes?termo=${encodeURIComponent(termo)}&pagina=${pagina}${fabrica ? `&fabrica_id=${fabrica}` : ''}`,
  )
  const ficha = useDados(
    clienteId ? `/clientes/${clienteId}?agrupar_rede=${rede}${fabrica ? `&fabrica_id=${fabrica}` : ''}` : null,
  )
  const cliente = ficha.dados
  // Lista e ficha compartilham a página, sem consultas desnecessárias da lista no detalhe.
  return (
    <main className="conteudo-painel" id="conteudo">
      <CabecalhoPagina
        titulo={clienteId ? 'Cliente 360º' : 'Sua carteira de clientes'}
        descricao={
          clienteId
            ? 'Histórico, ciclos e oportunidades em uma só visão.'
            : 'Conheça cada relacionamento. Prepare sua próxima visita.'
        }
      />
      {!clienteId && (
        <>
          <form
            className="filtros-comerciais faixa-filtros"
            onSubmit={(e) => {
              e.preventDefault()
              definirTermo(busca)
              definirPagina(1)
            }}
          >
            <label className="campo-busca">
              Nome, documento, rede ou cidade
              <input
                placeholder="Encontre um cliente na sua carteira…"
                value={busca}
                onChange={(e) => definirBusca(e.target.value)}
              />
            </label>
            <button className="botao-secundario">
              <Icone nome="busca" tamanho={17} /> Buscar
            </button>
            <FiltroFabrica fabricas={fabricas} valor={fabrica} aoMudar={(v) => { definirFabrica(v); definirPagina(1) }} />
            {lista.dados && (
              <span className="total-resultados">
                {lista.dados.total} clientes
              </span>
            )}
          </form>
          <EstadoConsulta
            carregando={lista.carregando}
            erro={lista.erro}
            vazio={lista.dados?.total === 0}
            mensagem="Nenhum cliente encontrado. Tente outro nome, rede ou cidade."
          />
          <div className="grade-cartoes">
            {lista.dados?.itens.map((c) => (
              <CartaoCliente key={c.id} cliente={c} aoAbrir={definirCliente} />
            ))}
          </div>
          {lista.dados && (
            <Paginacao
              pagina={pagina}
              total={lista.dados.total}
              tamanho={30}
              aoMudar={definirPagina}
              unidade="clientes"
            />
          )}
        </>
      )}
      {clienteId && (
        <div className="ficha-cliente">
          <button
            className="botao-texto voltar-clientes"
            onClick={() => {
              definirCliente(null)
              definirRede(true)
            }}
          >
            ← Voltar para clientes
          </button>
          <label className="opcao-rede">
            <input
              type="checkbox"
              checked={rede}
              onChange={(e) => definirRede(e.target.checked)}
            />{' '}
            Cliente comercial: agrupar todos os CNPJs da rede
          </label>
          <div className="filtros-comerciais"><FiltroFabrica fabricas={fabricas} valor={fabrica} aoMudar={definirFabrica} /></div>
          {ficha.erro && <p role="alert">{ficha.erro}</p>}
          {ficha.carregando && <p role="status">Analisando histórico…</p>}
          {cliente && (
            <>
              <section className="hero-cliente">
                <span className="sobretitulo">FICHA DO CLIENTE</span>
                <h2>{cliente.razao_social}</h2>
                <p>
                  {cliente.grupo_economico || 'Cliente individual'} ·{' '}
                  {cliente.clientes_agrupados} cadastro(s) fiscal(is)
                </p>
              </section>
              <div className="grade-indicadores">
                <CartaoIndicador
                  titulo="Valor comprado"
                  valor={formatarMoeda(cliente.valor_comprado)}
                  detalhe="Histórico completo"
                />
                <CartaoIndicador
                  titulo="Pedidos emitidos"
                  valor={cliente.pedidos_emitidos}
                  detalhe="Inclui pedidos diretos de fábrica"
                />
              </div>
              <Cartao titulo="Cadastros fiscais do cliente">
                <ul>{cliente.cadastros_fiscais?.map((c) => <li key={c.id}>
                  {c.razao_social} · {c.cnpj_cpf || 'Documento não informado'}
                  {rede && <button className="botao-texto" onClick={() => { definirCliente(c.id); definirRede(false) }}>Consultar este CNPJ</button>}
                </li>)}</ul>
              </Cartao>
              <RitmoCompras
                ritmo={cliente.ritmo_compras}
                produtos={cliente.comparacao_produtos || []}
              />
              <Cartao titulo="Fábricas e inatividade">
                <div className="rolagem-tabela">
                  <table>
                    <thead>
                      <tr>
                        <th>Fábrica</th>
                        <th>Última compra</th>
                        <th>Data limite</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cliente.resumo_fabricas.map((f) => (
                        <tr key={f.fabrica_id}>
                          <th>{f.fabrica}</th>
                          <td>{f.ultima_compra}</td>
                          <td>{f.data_limite_inatividade}</td>
                          <td>{f.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Cartao>
              <div className="grade-resumos">
                <Cartao titulo="Reposição de produtos">
                  {cliente.sugestoes_reposicao.length ? (
                    <ul>
                      {cliente.sugestoes_reposicao.map((p) => (
                        <li key={p.produto_id}>
                          Código {p.sku} · {p.nome}: {p.status} · volume habitual{' '}
                          {p.volume_habitual}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>Nenhuma reposição identificada neste momento.</p>
                  )}
                </Cartao>
                <Cartao titulo="Produtos em abandono">
                  {cliente.produtos_em_abandono.length ? (
                    <ul>
                      {cliente.produtos_em_abandono.map((p) => (
                        <li key={p.produto_id}>
                          Código {p.sku} · {p.nome}: {p.dias_parado} dias sem comprar.
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>Nenhum abandono identificado.</p>
                  )}
                </Cartao>
                <Cartao titulo="Completar o mix">
                  {cliente.sugestoes_expansao_mix.length ? (
                    <ul>
                      {cliente.sugestoes_expansao_mix.map((p) => (
                        <li key={p.produto_id}>
                          <strong>Código {p.sku} · {p.nome}</strong>
                          <p>
                            {p.motivo} · volume sugerido:{' '}
                            {p.volume_sugerido_unidades}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>
                      Ainda não há histórico semelhante suficiente para sugerir
                      produtos.
                    </p>
                  )}
                </Cartao>
                <Cartao titulo="Sugestões de fábricas">
                  {cliente.sugestoes_fabricas.length ? (
                    <ul>
                      {cliente.sugestoes_fabricas.map((f) => (
                        <li key={f.id}>
                          <strong>{f.nome}</strong>
                          <p>{f.motivo}</p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>
                      Nenhuma sugestão de nova fábrica com o histórico
                      disponível.
                    </p>
                  )}
                </Cartao>
              </div>
              <p className="nota-painel">
                Inatividade de fábrica: 90 dias. O ciclo de reposição utiliza as
                datas de compra do histórico.
              </p>
            </>
          )}
        </div>
      )}
    </main>
  )
}
