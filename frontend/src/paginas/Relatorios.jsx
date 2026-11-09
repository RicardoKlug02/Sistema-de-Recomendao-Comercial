import { useEstadoPagina } from '../hooks/estadoPaginas'
import Pagina from '../componentes/Pagina'
import Seletor from '../componentes/Seletor'
import RelatorioOperacional from '../componentes/relatorios/RelatorioOperacional'
import RelatorioRede from '../componentes/relatorios/RelatorioRede'
import { tiposRelatorio } from '../servicos/relatorios'

export default function Relatorios({ fabricas = [], vendedores = [] }) {
  const [tipo, setTipo] = useEstadoPagina('relatorios.tipo', 'rede')
  return <Pagina titulo="Relatórios" descricao="Carteira, recuperação, preços e regiões a partir do histórico importado.">
    <div className="filtros-comerciais faixa-filtros"><Seletor rotulo="Relatório" opcoes={tiposRelatorio} valor={tipo} aoMudar={setTipo} /></div>
    {tipo === 'rede' ? <RelatorioRede fabricas={fabricas} /> : <RelatorioOperacional key={tipo} tipo={tipo} fabricas={fabricas} vendedores={vendedores} />}
  </Pagina>
}
