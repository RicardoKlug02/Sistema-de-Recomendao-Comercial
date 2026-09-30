import { useState } from 'react'
import Importacao from './Importacao'
import Clientes from './Clientes'
import Alertas from './Alertas'
import Usuarios from './Usuarios'
import MenuLateral from '../componentes/MenuLateral'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import useDados from '../servicos/useDados'
import { formatarMoeda } from '../servicos/dadosPainel'
import './PainelComercial.css'
import './Operacao.css'

export default function PainelComercial({ usuario, aoSair, referenciaTitulo }) {
  const [secao, definirSecao] = useState('painel')
  const [mes, definirMes] = useState('')
  const [vendedor, definirVendedor] = useState('')
  const [clienteId, definirCliente] = useState(null)
  const [versao, definirVersao] = useState(0)
  const cadastroVendedores = useDados('/comercial/vendedores', versao)
  const consulta = useDados(secao === 'painel' ? `/comercial/painel?${mes ? `mes=${mes}&` : ''}${vendedor ? `vendedor_id=${vendedor}` : ''}` : null, versao)
  const dados = consulta.dados
  const indicadores = dados?.indicadores
  const maior = Math.max(1, ...(dados?.faturamento_mensal || []).map((m) => m.valor))
  function abrirCliente(id) { definirCliente(id); definirSecao('clientes') }
  function navegar(destino) { if (destino === 'clientes') definirCliente(null); definirSecao(destino) }
  return <div className="estrutura-painel">
    <MenuLateral usuario={usuario} aoSair={aoSair} secaoAtiva={secao} aoNavegar={navegar} />
    {secao === 'importacoes' && <Importacao usuario={usuario} aoImportar={() => definirVersao((v) => v + 1)} />}
    {secao === 'clientes' && <Clientes key={clienteId || 'lista'} inicial={clienteId} />}
    {secao === 'alertas' && <Alertas vendedores={cadastroVendedores.dados || []} aoAbrirCliente={abrirCliente} />}
    {secao === 'usuarios' && <Usuarios />}
    {secao === 'painel' && <main className="conteudo-painel">
      <header className="cabecalho-painel"><div><p className="sobretitulo">VISÃO COMERCIAL</p><h1 ref={referenciaTitulo} tabIndex={-1}>Dashboard</h1><p>Indicadores dos pedidos importados</p></div></header>
      <div className="filtros-comerciais">
        <label>Mês<input type="month" value={mes || dados?.mes || ''} onChange={(e) => definirMes(e.target.value)} /></label>
        <label>Vendedor<select value={vendedor} onChange={(e) => definirVendedor(e.target.value)}><option value="">Todos os vendedores</option>{cadastroVendedores.dados?.map((v) => <option key={v.id} value={v.id}>{v.nome}</option>)}</select></label>
        <button className="botao-secundario" onClick={() => definirVersao((v) => v + 1)}>Atualizar</button>
      </div>
      {(consulta.erro || cadastroVendedores.erro) && <p className="erro-campo" role="alert">{consulta.erro || cadastroVendedores.erro}</p>}
      {consulta.carregando && <p role="status">Carregando indicadores…</p>}
      {indicadores && <>
        <div className="grade-indicadores">{[
          ['Venda total', formatarMoeda(indicadores.venda_total)], ['Pedidos emitidos', indicadores.pedidos_emitidos],
          ['Clientes atendidos', indicadores.clientes_atendidos], ['Ticket médio', formatarMoeda(indicadores.ticket_medio)],
          ['Novos clientes no escritório', indicadores.clientes_novos], ['Aberturas cliente–fábrica', indicadores.aberturas_cliente_fabrica], ['Clientes reativados', indicadores.clientes_reativados],
        ].map(([titulo, valor]) => <CartaoIndicador key={titulo} titulo={titulo} valor={valor} detalhe="Período selecionado" />)}</div>
        {indicadores.pedidos_emitidos === 0 && <p>Nenhum pedido no período. Importe as planilhas ou escolha outro mês.</p>}
        <div className="grade-resumos">
          <Cartao titulo="Clientes abertos por fábrica" descricao="Primeira compra de cada cliente na fábrica, conforme o histórico importado"><ul>{dados.aberturas?.map((a) => <li key={`${a.cliente_id}:${a.fabrica}`}><button className="botao-detalhes" onClick={() => abrirCliente(a.cliente_id)}>{a.cliente}</button> · {a.fabrica} · {a.data}{a.novo_no_escritorio ? ' · Primeiro pedido no escritório' : ''}</li>)}</ul>{!dados.aberturas?.length && <p>Nenhuma abertura no período.</p>}</Cartao>
          <Cartao titulo="Faturamento mensal" descricao="12 meses até o período selecionado"><div className="grafico-colunas" role="list">
            {dados.faturamento_mensal.map((m) => <div className="coluna-mensal" role="listitem" tabIndex={0} key={m.mes} aria-label={`${m.mes}: ${formatarMoeda(m.valor)}`}>
              <span className="valor-coluna">{formatarMoeda(m.valor)}</span><div className="trilho-coluna" aria-hidden="true"><span style={{ height: `${m.valor / maior * 100}%` }} /></div><span>{m.mes.slice(5)}/{m.mes.slice(2, 4)}</span>
            </div>)}</div></Cartao>
          <Cartao titulo="Fábricas mais vendidas"><ol className="lista-clientes">{dados.fabricas.map((f) => <li key={f.id}><span>{f.nome}</span><strong>{formatarMoeda(f.valor)}</strong></li>)}</ol></Cartao>
          <Cartao titulo="Vendas por região imediata" descricao="Região consultada no IBGE a partir da cidade e UF do cliente"><ol className="lista-clientes">{dados.regioes?.map((r) => <li key={`${r.uf}:${r.nome}`}><span>{r.nome} · {r.uf}</span><strong>{formatarMoeda(r.valor)}</strong></li>)}</ol>{!dados.regioes?.length && <p>Sem vendas no período.</p>}</Cartao>
          <Cartao titulo="Produtos quentes" descricao="Ranking por valor de itens vendidos no período"><ol className="lista-clientes">{dados.produtos.map((p) => <li key={p.id}><span>{p.nome} · {p.quantidade} un.</span><strong>{formatarMoeda(p.valor)}</strong></li>)}</ol>{!dados.produtos.length && <p>Sem itens de produtos no período.</p>}</Cartao>
          <Cartao titulo="Principais clientes"><ol className="lista-clientes">{dados.clientes.map((c) => <li key={c.id}><button className="botao-detalhes" onClick={() => abrirCliente(c.id)}>{c.nome}</button><strong>{formatarMoeda(c.valor)}</strong></li>)}</ol></Cartao>
          <Cartao titulo="Fábricas quentes" descricao="Crescimento sobre o mês anterior"><ul>{dados.fabricas_quentes.map((f) => <li key={f.nome}>{f.nome}: +{f.crescimento}%</li>)}</ul>{!dados.fabricas_quentes.length && <p>Sem crescimento comparável no período.</p>}</Cartao>
          <Cartao titulo="Acompanhamento comercial"><p>Consulte a central para contatos de segundo pedido, fábricas próximas da inatividade e produtos em risco.</p><button className="botao-secundario" onClick={() => definirSecao('alertas')}>Abrir central de alertas</button></Cartao>
        </div>
        <p className="nota-painel">Primeiras compras são identificadas pelo histórico importado. Um novo cliente no escritório também conta como abertura na fábrica; um cliente pode abrir em várias fábricas. {indicadores.pedidos_sem_itens} pedidos sem itens no período. Incluídos no faturamento; o ranking de produtos considera apenas itens informados. Reativação: retorno após 90 dias sem compra.</p>
      </>}
    </main>}
  </div>
}
