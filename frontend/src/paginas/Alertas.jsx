import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import useDados from '../servicos/useDados'

const tipos = { SEGUNDO_PEDIDO: 'Segundo pedido', CLIENTE_INATIVO: 'Cliente inativo',
  FABRICA_EM_RISCO: 'Fábrica próxima da inatividade', FABRICA_INATIVA: 'Fábrica inativa', PRODUTO_EM_RISCO: 'Produto em risco' }

export default function Alertas({ vendedores, aoAbrirCliente }) {
  const [tipo, definirTipo] = useState('')
  const [vendedor, definirVendedor] = useState('')
  const [pagina, definirPagina] = useState(1)
  const resposta = useDados(`/comercial/alertas?pagina=${pagina}&tipo=${tipo}${vendedor ? `&vendedor_id=${vendedor}` : ''}`)
  return <main className="conteudo-painel"><header className="cabecalho-painel"><div><h1>Central de alertas</h1><p>Priorize os contatos com base no histórico de compra.</p></div></header>
    <div className="filtros-comerciais"><label>Tipo<select value={tipo} onChange={(e) => { definirTipo(e.target.value); definirPagina(1) }}><option value="">Todos</option>{Object.entries(tipos).map(([chave, nome]) => <option key={chave} value={chave}>{nome}</option>)}</select></label>
      <label>Vendedor<select value={vendedor} onChange={(e) => { definirVendedor(e.target.value); definirPagina(1) }}><option value="">Todos</option>{vendedores.map((v) => <option key={v.id} value={v.id}>{v.nome}</option>)}</select></label></div>
    <Cartao titulo="Ações comerciais">
      {resposta.erro && <p role="alert">{resposta.erro}</p>}
      {resposta.carregando ? <p role="status">Calculando alertas…</p> : <div className="rolagem-tabela"><table><thead><tr><th>Cliente</th><th>Alerta</th><th>Ação recomendada</th><th>Prioridade</th><th>Ficha</th></tr></thead>
        <tbody>{resposta.dados?.itens.map((a) => <tr key={a.id}><th>{a.cliente}</th><td>{tipos[a.tipo]}</td><td>{a.descricao}</td><td>{a.prioridade === 1 ? 'Alta' : 'Acompanhamento'}</td><td><button className="botao-detalhes" onClick={() => aoAbrirCliente(a.cliente_id)}>Cliente 360º</button></td></tr>)}</tbody></table>
        {resposta.dados?.total === 0 && <p>Nenhum alerta para os filtros selecionados.</p>}</div>}
      <div className="paginacao-importacao"><button className="botao-secundario" disabled={pagina === 1} onClick={() => definirPagina(pagina - 1)}>Anterior</button><span>{resposta.dados?.total ?? 0} alertas</span>
        <button className="botao-secundario" disabled={!resposta.dados || pagina * 50 >= resposta.dados.total} onClick={() => definirPagina(pagina + 1)}>Próxima</button></div>
    </Cartao>
    <p className="nota-painel">Segundo pedido após 14 dias; fábricas em risco a partir de 76 dias e inativas a partir de 90. Alertas são recalculados ao consultar.</p>
  </main>
}
