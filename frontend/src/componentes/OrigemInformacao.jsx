import { formatarData } from '../servicos/formatacao'

export default function OrigemInformacao({ origem, pedidos, titulo = 'Ver pedidos usados nesta análise' }) {
  const registros = pedidos || origem?.pedidos || []
  if (!registros.length) return null
  return <details className="entenda-indicador">
    <summary>{titulo} ({registros.length})</summary>
    <p>{origem?.fonte || 'Cabeçalhos dos pedidos importados'}. Consulte o relatório original para conferir os dados.</p>
    <div className="rolagem-tabela"><table>
      <thead><tr><th>Pedido</th><th>Data</th><th>Cadastro fiscal</th><th>CNPJ/CPF</th><th>Fábrica</th><th>Código original</th></tr></thead>
      <tbody>{registros.map((p, i) => <tr key={`${p.venda_id}-${i}`}>
        <td>{p.pedido || `Registro ${p.venda_id}`}</td><td>{formatarData(p.data)}</td>
        <td>{p.cliente || 'Não informado'}</td><td>{p.cnpj_cpf || 'Não informado'}</td>
        <td>{p.fabrica || '—'}</td><td>{p.codigos?.join(', ') || '—'}</td>
      </tr>)}</tbody>
    </table></div>
  </details>
}
