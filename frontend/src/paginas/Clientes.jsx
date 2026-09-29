import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import useDados from '../servicos/useDados'
import { formatarMoeda } from '../servicos/dadosPainel'

export default function Clientes({ inicial = null }) {
  const [busca, definirBusca] = useState('')
  const [termo, definirTermo] = useState('')
  const [pagina, definirPagina] = useState(1)
  const [clienteId, definirCliente] = useState(inicial)
  const [rede, definirRede] = useState(false)
  const lista = useDados(`/comercial/clientes?termo=${encodeURIComponent(termo)}&pagina=${pagina}`)
  const ficha = useDados(clienteId ? `/clientes/${clienteId}?agrupar_rede=${rede}` : null)
  const cliente = ficha.dados
  return <main className="conteudo-painel">
    <header className="cabecalho-painel"><div><h1>Cliente 360º</h1><p>Histórico de compra, ciclos e oportunidades.</p></div></header>
    <Cartao titulo="Encontrar cliente">
      <form className="filtros-comerciais" onSubmit={(e) => { e.preventDefault(); definirTermo(busca); definirPagina(1) }}>
        <label>Nome, documento, rede ou cidade<input value={busca} onChange={(e) => definirBusca(e.target.value)} /></label>
        <button className="botao-secundario">Buscar</button>
      </form>
      {lista.erro && <p role="alert">{lista.erro}</p>}
      {lista.carregando ? <p role="status">Carregando clientes…</p> : <div className="rolagem-tabela"><table>
        <thead><tr><th>Cliente</th><th>Rede</th><th>Cidade</th><th>Ação</th></tr></thead>
        <tbody>{lista.dados?.itens.map((c) => <tr key={c.id}><th>{c.razao_social}</th><td>{c.grupo_economico || '—'}</td><td>{c.cidade || '—'}</td><td><button className="botao-detalhes" onClick={() => definirCliente(c.id)}>Abrir ficha</button></td></tr>)}</tbody>
      </table>{lista.dados?.total === 0 && <p>Nenhum cliente encontrado.</p>}</div>}
      <div className="paginacao-importacao"><button className="botao-secundario" disabled={pagina === 1} onClick={() => definirPagina(pagina - 1)}>Anterior</button>
        <span>Página {pagina} · {lista.dados?.total ?? 0} clientes</span>
        <button className="botao-secundario" disabled={!lista.dados || pagina * 30 >= lista.dados.total} onClick={() => definirPagina(pagina + 1)}>Próxima</button></div>
    </Cartao>
    {clienteId && <div className="ficha-cliente">
      <label className="opcao-rede"><input type="checkbox" checked={rede} onChange={(e) => definirRede(e.target.checked)} /> Agrupar compras da rede de clientes</label>
      {ficha.erro && <p role="alert">{ficha.erro}</p>}
      {ficha.carregando && <p role="status">Analisando histórico…</p>}
      {cliente && <>
        <h2>{cliente.razao_social}</h2><p>{cliente.grupo_economico || 'Cliente individual'} · {cliente.clientes_agrupados} estabelecimento(s)</p>
        <div className="grade-indicadores"><CartaoIndicador titulo="Valor comprado" valor={formatarMoeda(cliente.valor_comprado)} detalhe="Histórico completo" />
          <CartaoIndicador titulo="Pedidos emitidos" valor={cliente.pedidos_emitidos} detalhe="Inclui pedidos diretos de fábrica" /></div>
        <Cartao titulo="Fábricas e inatividade"><div className="rolagem-tabela"><table><thead><tr><th>Fábrica</th><th>Última compra</th><th>Data limite</th><th>Status</th></tr></thead>
          <tbody>{cliente.resumo_fabricas.map((f) => <tr key={f.fabrica_id}><th>{f.fabrica}</th><td>{f.ultima_compra}</td><td>{f.data_limite_inatividade}</td><td>{f.status}</td></tr>)}</tbody></table></div></Cartao>
        <div className="grade-resumos">
          <Cartao titulo="Reposição de produtos">{cliente.sugestoes_reposicao.length ? <ul>{cliente.sugestoes_reposicao.map((p) => <li key={p.produto_id}>{p.nome}: {p.status} · volume habitual {p.volume_habitual}</li>)}</ul> : <p>Nenhuma reposição identificada neste momento.</p>}</Cartao>
          <Cartao titulo="Produtos em abandono">{cliente.produtos_em_abandono.length ? <ul>{cliente.produtos_em_abandono.map((p) => <li key={p.produto_id}>{p.nome}: {p.dias_parado} dias sem comprar.</li>)}</ul> : <p>Nenhum abandono identificado.</p>}</Cartao>
          <Cartao titulo="Completar o mix">{cliente.sugestoes_expansao_mix.length ? <ul>{cliente.sugestoes_expansao_mix.map((p) => <li key={p.produto_id}><strong>{p.nome}</strong><p>{p.motivo} · volume sugerido: {p.volume_sugerido_unidades}</p></li>)}</ul> : <p>Ainda não há histórico semelhante suficiente para sugerir produtos.</p>}</Cartao>
          <Cartao titulo="Sugestões de fábricas">{cliente.sugestoes_fabricas.length ? <ul>{cliente.sugestoes_fabricas.map((f) => <li key={f.id}><strong>{f.nome}</strong><p>{f.motivo}</p></li>)}</ul> : <p>Nenhuma sugestão de nova fábrica com o histórico disponível.</p>}</Cartao>
        </div>
        <p className="nota-painel">Inatividade de fábrica: 90 dias. O ciclo de reposição utiliza as datas de compra do histórico.</p>
      </>}
    </div>}
  </main>
}
