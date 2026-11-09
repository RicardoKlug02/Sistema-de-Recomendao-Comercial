import { useEstadoPagina } from '../../hooks/estadoPaginas'
import useAcao from '../../hooks/useAcao'
import useDados from '../../hooks/useDados'
import { baixarArquivo, montarCaminho } from '../../servicos/api'
import { formatarData, formatarMoeda } from '../../servicos/formatacao'
import Cartao from '../Cartao'
import EstadoConsulta from '../EstadoConsulta'
import Seletor from '../Seletor'
import Tabela from '../Tabela'

export default function RelatorioRede({ fabricas }) {
  const [rede, definirRede] = useEstadoPagina('relatorioRede.rede', '')
  const [fabrica, definirFabrica] = useEstadoPagina('relatorioRede.fabrica', '')
  const download = useAcao()
  const redes = useDados('/relatorios/redes')
  const parametros = { rede, fabrica_id: fabrica }
  const consulta = useDados(rede ? montarCaminho('/relatorios/produtos-rede', parametros) : null)
  const opcoesRede = (redes.dados || []).map((r) => ({ id: r.nome, nome: `${r.nome} (${r.clientes} cadastros fiscais)` }))
  return (
    <Cartao titulo="Códigos comprados pela rede" descricao="Último pedido e último preço unitário por produto, considerando todos os CNPJs da rede.">
      <div className="filtros-comerciais faixa-filtros">
        <Seletor rotulo="Rede de clientes" todos="Selecione uma rede" opcoes={opcoesRede} valor={rede} disabled={download.executando}
          aoMudar={(v) => { definirRede(v); download.definirErro('') }} />
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={definirFabrica} disabled={download.executando} />
        <button className="botao-principal" disabled={!rede || consulta.carregando || !consulta.dados || download.executando}
          onClick={() => download.executar(() => baixarArquivo(montarCaminho('/relatorios/produtos-rede/pdf', parametros), 'produtos-da-rede.pdf'))}>
          {download.executando ? 'Gerando PDF…' : 'Baixar PDF'}
        </button>
      </div>
      <EstadoConsulta carregando={redes.carregando || consulta.carregando} erro={download.erro || redes.erro || consulta.erro}
        aoTentar={() => { download.definirErro(''); redes.tentarNovamente(); consulta.tentarNovamente() }} />
      {!redes.carregando && redes.dados?.length === 0 && <p>Não há redes cadastradas. Preencha a coluna Rede de clientes na importação.</p>}
      {consulta.dados && <>
        <p>{consulta.dados.clientes} cadastros fiscais · {consulta.dados.total} {consulta.dados.total === 1 ? 'código encontrado' : 'códigos encontrados'}.</p>
        <Tabela colunas={['Código', 'Produto', 'Fábrica', 'Último pedido', 'Último preço unitário', 'Pedido', 'Cliente da compra']}>
          {consulta.dados.produtos.map((p) => <tr key={p.produto_id}><td>{p.sku}</td><td>{p.nome}</td><td>{p.fabrica}</td><td>{formatarData(p.ultima_compra)}</td><td className="valor-numerico">{formatarMoeda(p.ultimo_preco)}</td><td>{p.pedido}</td><td>{p.cliente}</td></tr>)}
        </Tabela>
        {!consulta.dados.total && <p>Nenhum produto comprado com os filtros selecionados.</p>}
        <p className="nota-painel">{consulta.dados.pedidos_sem_itens} pedidos sem itens. Códigos e preços desses pedidos não estão disponíveis. O último preço pertence à última compra encontrada na rede, no histórico importado.</p>
      </>}
    </Cartao>
  )
}
