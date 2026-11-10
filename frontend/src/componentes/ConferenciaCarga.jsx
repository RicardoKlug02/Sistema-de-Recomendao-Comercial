import { formatarData, formatarMoeda } from '../servicos/formatacao'

export default function ConferenciaCarga({ carga }) {
  const base = carga.conferencia_base
  if (!base) return <p>Esta carga antiga não possui conferência final registrada.</p>
  return <section aria-label="Conferência final da importação">
    <h3>Conferência após a importação</h3>
    <p>Posição salva ao concluir a carga, de {formatarData(base.inicio)} a {formatarData(base.fim)}. Alterações posteriores podem modificar a posição atual.</p>
    <ul>
      <li>Arquivo: {carga.processados} pedidos processados · {formatarMoeda(carga.valor_arquivo)}</li>
      <li>Base no período: {base.pedidos_compra} pedidos de compra · {base.linhas_itens} linhas de itens</li>
      <li>Valor comissionado na base: {formatarMoeda(base.valor_comissionado)} · {base.ajustes_comissionados} ajustes sem nova compra</li>
      <li>{base.fora_analises} registros fora das análises · {carga.desconsiderados_por_tipo ?? 0} pedidos desconsiderados por tipo nos arquivos</li>
      <li>{base.pedidos_sem_itens} compras sem itens na base · {base.pendentes_sem_itens} pendentes de revisão</li>
    </ul>
    <p>Compare com o Mercos no mesmo período. Os totais do arquivo e da base podem diferir por pedidos já existentes, classificações manuais e ajustes comissionados. A gravação concluída não certifica que a exportação esteja completa.</p>
  </section>
}
