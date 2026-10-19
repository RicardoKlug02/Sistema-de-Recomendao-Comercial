import useDados from '../servicos/useDados'
import { formatarData, formatarDataHora } from '../servicos/datas'

export default function HistoricoDisponivel({ versao }) {
  const consulta = useDados('/comercial/historico-disponivel', versao)
  const h = consulta.dados
  return <aside className="historico-disponivel" aria-label="Histórico disponível">
    {consulta.carregando && <span role="status">Consultando período disponível…</span>}
    {consulta.erro && <><span role="alert">Não foi possível consultar o histórico disponível.</span><button type="button" className="botao-texto" onClick={consulta.tentarNovamente}>Tentar novamente</button></>}
    {h && <>
      <strong>{h.inicio ? `Histórico disponível: ${formatarData(h.inicio)} a ${formatarData(h.fim)}` : 'Nenhum pedido importado'}</strong>
      <span>{h.pedidos.toLocaleString('pt-BR')} pedidos na base</span>
      <span>{h.ultima_importacao ? `Última importação: ${formatarDataHora(h.ultima_importacao.data)} · ${h.ultima_importacao.pedidos} pedidos processados` : 'Sem importação registrada'}</span>
      <details><summary>Entenda este histórico</summary><p>A faixa mostra a primeira e a última venda conhecidas; não confirma que todos os meses foram importados. Primeiras compras são sempre as primeiras registradas na base.</p></details>
    </>}
  </aside>
}
