import Cartao from './Cartao'
import { formatarMoeda } from '../servicos/dadosPainel'

const numero = (v) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 }).format(v)
const data = (v) => v.split('-').reverse().join('/')
const explicacoes = {
  HISTORICO_INSUFICIENTE: 'Histórico insuficiente',
  SEM_BASE_COMPARACAO: 'Sem base de comparação',
  ITENS_INCOMPLETOS: 'Há pedidos sem itens nesta fábrica',
}
function variacao(metrica) {
  return metrica.variacao_pct === null ? explicacoes[metrica.status] || '—'
    : `${metrica.variacao_pct > 0 ? '+' : ''}${numero(metrica.variacao_pct)}%`
}

export default function RitmoCompras({ ritmo, produtos }) {
  if (!ritmo) return null
  return <Cartao titulo="Ritmo de compras" descricao="Últimos 30 dias comparados com a média por 30 dias dos 90 dias anteriores">
    <p>Período recente: {data(ritmo.inicio_recente)} a {data(ritmo.fim_recente)}. Base habitual: {data(ritmo.inicio_habitual)} a {data(ritmo.fim_habitual)}.</p>
    <div className="rolagem-tabela"><table><thead><tr><th>Indicador</th><th>Média habitual por 30 dias</th><th>Últimos 30 dias</th><th>Variação</th></tr></thead>
      <tbody>{[['Valor comprado', ritmo.valor, formatarMoeda], ['Pedidos emitidos', ritmo.pedidos, numero]].map(([nome, metrica, formatar]) =>
        <tr key={nome}><th>{nome}</th><td>{formatar(metrica.media_habitual)}</td><td>{formatar(metrica.recente)}</td><td>{variacao(metrica)}</td></tr>)}</tbody>
    </table></div>
    {!ritmo.historico_suficiente && <p>Para calcular a variação, é necessário histórico desde o início do período habitual e pelo menos dois pedidos nos 90 dias anteriores.</p>}
    <p>Valores positivos indicam aumento; negativos indicam redução. Esta comparação não gera alertas automáticos.</p>
    <h3>Quantidades por produto</h3>
    {produtos.length ? <div className="rolagem-tabela"><table><thead><tr><th>Produto</th><th>Média habitual (un.)</th><th>Últimos 30 dias (un.)</th><th>Variação</th></tr></thead>
      <tbody>{produtos.map((p) => <tr key={p.produto_id}><th>{p.nome}<small> · {p.sku}</small></th>
        <td>{p.status === 'ITENS_INCOMPLETOS' ? '—' : numero(p.media_habitual)}</td><td>{p.status === 'ITENS_INCOMPLETOS' ? '—' : numero(p.recente)}</td><td>{variacao(p)}</td></tr>)}</tbody>
    </table></div> : <p>Sem histórico de itens nesses períodos para comparar quantidades.</p>}
    <p>Pedidos sem itens entram no valor e no número de pedidos. Se houver pedidos sem itens de uma fábrica nos períodos comparados, as quantidades dos seus produtos não são comparadas.</p>
  </Cartao>
}
