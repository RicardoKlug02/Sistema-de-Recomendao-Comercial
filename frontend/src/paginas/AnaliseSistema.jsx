import { DATA_IMPLANTACAO } from '../configuracao'
import { useEstadoPagina } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Pagina from '../componentes/Pagina'
import Seletor from '../componentes/Seletor'
import Tabela from '../componentes/Tabela'
import { montarCaminho } from '../servicos/api'
import { comSinal, dataLocal, formatarData } from '../servicos/formatacao'

const metricas = [
  ['clientes_inativos', 'Clientes inativos', '90 dias ou mais sem compra'],
  ['relacoes_inativas', 'Relações cliente x fábrica inativas', '90 dias ou mais sem compra na fábrica'],
  ['itens_inativos', 'Produtos em abandono', 'Cliente x código: regra do ciclo habitual'],
  ['clientes_reativados', 'Clientes reativados', 'Períodos anteriores e posteriores de igual duração'],
]
const taxa = (valor) => (valor === null ? 'Sem base' : `${valor}%`)

export default function AnaliseSistema({ fabricas = [], vendedores = [] }) {
  const [implantacao, setImplantacao] = useEstadoPagina('analise.implantacao', DATA_IMPLANTACAO)
  const [fim, setFim] = useEstadoPagina('analise.fim', dataLocal())
  const [fabrica, setFabrica] = useEstadoPagina('analise.fabrica', '')
  const [vendedor, setVendedor] = useEstadoPagina('analise.vendedor', '')
  const valido = implantacao && fim && implantacao <= fim && fim <= dataLocal()
  const resposta = useDados(valido ? montarCaminho('/analises/impacto', { implantacao, fim, fabrica_id: fabrica, vendedor_id: vendedor }) : null)
  const d = resposta.dados
  return <Pagina titulo="Análise do sistema" descricao="Como a carteira evoluiu antes e depois da implantação.">
    <div className="filtros-comerciais faixa-filtros">
      <label>Início da implantação<input type="date" value={implantacao} max={fim} onChange={(e) => setImplantacao(e.target.value)} /></label>
      <label>Acompanhar até<input type="date" value={fim} max={dataLocal()} onChange={(e) => setFim(e.target.value)} /></label>
      <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={setFabrica} />
      <Seletor rotulo="Vendedor" todos="Toda a equipe" opcoes={vendedores} valor={vendedor} aoMudar={setVendedor} />
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
        <Tabela colunas={['Indicador', 'Antes', 'Depois', 'Diferença', 'Critério']}>
          {metricas.map(([chave, nome, criterio]) => <tr key={chave}><th>{nome}</th><td>{d.antes[chave]}</td><td>{d.depois[chave]}</td><td>{comSinal(d.depois[chave] - d.antes[chave])}</td><td>{criterio}</td></tr>)}
        </Tabela>
        <p>Taxa de clientes inativos na carteira inicial: {taxa(d.antes.taxa_inatividade)} antes; {taxa(d.depois.taxa_inatividade)} depois.</p>
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
  </Pagina>
}
