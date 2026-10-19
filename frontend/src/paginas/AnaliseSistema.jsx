import { useEstadoPagina } from '../servicos/estadoPaginas'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import FiltroFabrica from '../componentes/comercial/FiltroFabrica'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import useDados from '../servicos/useDados'
import { dataLocal, formatarData } from '../servicos/datas'

const metricas = [
  ['clientes_inativos', 'Clientes inativos', '90 dias ou mais sem compra'],
  ['relacoes_inativas', 'Relações cliente x fábrica inativas', '90 dias ou mais sem compra na fábrica'],
  ['itens_inativos', 'Produtos em abandono', 'Cliente x código: regra do ciclo habitual'],
  ['clientes_reativados', 'Clientes reativados', 'Períodos anteriores e posteriores de igual duração'],
]
export default function AnaliseSistema({ fabricas = [], vendedores = [] }) {
  const [implantacao, setImplantacao] = useEstadoPagina('analise.implantacao', '2026-09-29')
  const [fim, setFim] = useEstadoPagina('analise.fim', dataLocal())
  const [fabrica, setFabrica] = useEstadoPagina('analise.fabrica', '')
  const [vendedor, setVendedor] = useEstadoPagina('analise.vendedor', '')
  const parametros = new URLSearchParams({ implantacao, fim })
  if (fabrica) parametros.set('fabrica_id', fabrica)
  if (vendedor) parametros.set('vendedor_id', vendedor)
  const valido = implantacao && fim && implantacao <= fim && fim <= dataLocal()
  const resposta = useDados(valido ? `/analises/impacto?${parametros}` : null)
  const d = resposta.dados
  return <main className="conteudo-painel" id="conteudo">
    <CabecalhoPagina titulo="Análise do sistema" descricao="Como a carteira evoluiu antes e depois da implantação." />
    <div className="filtros-comerciais faixa-filtros">
      <label>Início da implantação<input type="date" value={implantacao} max={fim} onChange={(e) => setImplantacao(e.target.value)} /></label>
      <label>Acompanhar até<input type="date" value={fim} max={dataLocal()} onChange={(e) => setFim(e.target.value)} /></label>
      <FiltroFabrica fabricas={fabricas} valor={fabrica} aoMudar={setFabrica} />
      <label>Vendedor<select aria-label="Vendedor" value={vendedor} onChange={(e) => setVendedor(e.target.value)}><option value="">Toda a equipe</option>{vendedores.map((v) => <option key={v.id} value={v.id}>{v.nome}</option>)}</select></label>
    </div>
    {!valido && <p role="alert">Informe datas válidas, com fim igual ou posterior à implantação e até hoje.</p>}
    <EstadoConsulta carregando={resposta.carregando} erro={resposta.erro} aoTentar={resposta.tentarNovamente} />
    {d && <>
      <div className="grade-indicadores">
        <CartaoIndicador titulo="Clientes da carteira inicial" valor={d.antes.clientes_total} detalhe={`Conhecidos até ${formatarData(d.base)}`} />
        <CartaoIndicador titulo="Inativos iniciais que compraram novamente" valor={d.inativos_iniciais_recuperados} detalhe="Retomaram compras após a implantação" />
        <CartaoIndicador titulo="Reativados após a implantação" valor={d.depois.clientes_reativados} detalhe={`${d.dias_periodo} dias de acompanhamento`} />
        <CartaoIndicador titulo="Novos clientes na base" valor={d.novos_clientes} detalhe="Primeira compra registrada na base, no escopo selecionado" />
      </div>
      <Cartao titulo="Antes e depois, acompanhando os mesmos clientes">
        <p>Escopo: {d.escopo}. Posições em {formatarData(d.base)} e {formatarData(d.fim)}.</p>
        <p>Reativações: {formatarData(d.periodo_antes.inicio)} a {formatarData(d.periodo_antes.fim)} versus {formatarData(d.periodo_depois.inicio)} a {formatarData(d.periodo_depois.fim)} — {d.dias_periodo} dias em cada período.</p>
        <div className="rolagem-tabela"><table><thead><tr><th>Indicador</th><th>Antes</th><th>Depois</th><th>Diferença</th><th>Critério</th></tr></thead><tbody>
          {metricas.map(([chave, nome, criterio]) => { const delta = d.depois[chave] - d.antes[chave]; return <tr key={chave}><th>{nome}</th><td>{d.antes[chave]}</td><td>{d.depois[chave]}</td><td>{delta > 0 ? '+' : ''}{delta}</td><td>{criterio}</td></tr> })}
        </tbody></table></div>
        <p>Taxa de clientes inativos na carteira inicial: {d.antes.taxa_inatividade === null ? 'Sem base' : `${d.antes.taxa_inatividade}%`} antes; {d.depois.taxa_inatividade === null ? 'Sem base' : `${d.depois.taxa_inatividade}%`} depois.</p>
        <p>Produtos em abandono: ao menos três datas de compra, 60 dias sem comprar e mais de 2,5 vezes o ciclo médio histórico. Não são unidades: cada relação cliente x código conta uma vez.</p>
        <p>{d.antes.itens_sem_confirmacao} relações cliente x código sem confirmação antes e {d.depois.itens_sem_confirmacao} depois, por haver pedidos sem itens posteriores à última compra conhecida. Não são contadas como abandono confirmado.</p>
        <p>{d.antes.itens_total} relações cliente x código e os mesmos {d.antes.clientes_total} clientes compõem a base fixa do comparativo.</p>
        <p>Novos clientes são identificados pela primeira compra registrada na base. Importar históricos anteriores pode alterar essa classificação e a composição da carteira inicial.</p>
        {!d.antes.clientes_total && <p role="status">Sem clientes conhecidos antes da implantação para comparar. Importe o histórico anterior; primeiras compras registradas na base aparecem separadamente.</p>}
        {!d.historico_90_dias && <p role="status">O histórico não alcança 90 dias antes da base. Os números podem subestimar a inatividade anterior.</p>}
        <p className="nota-painel">Histórico disponível desde {formatarData(d.historico_desde)}. {d.nota}</p>
        <p className="nota-painel">Esta análise ainda não vincula contatos ou ações do vendedor aos pedidos. A melhora observada não pode ser atribuída automaticamente ao sistema.</p>
      </Cartao>
    </>}
  </main>
}
