import { DATA_IMPLANTACAO, TAMANHO_PAGINA } from '../../configuracao'
import { useEstadoPagina, useRolagemPagina } from '../../hooks/estadoPaginas'
import useAcao from '../../hooks/useAcao'
import useDados from '../../hooks/useDados'
import { baixarArquivo, montarCaminho } from '../../servicos/api'
import { dataLocal, diasAtras, formatarValor } from '../../servicos/formatacao'
import { ehRelatorioDePosicao, tiposRelatorio } from '../../servicos/relatorios'
import Cartao from '../Cartao'
import EstadoConsulta from '../EstadoConsulta'
import Paginacao from '../Paginacao'
import Seletor from '../Seletor'
import Tabela from '../Tabela'

const tiposReativacao = { cliente: 'Cliente no escritório', fabrica: 'Cliente x fábrica' }
const formatosNumericos = ['moeda', 'numero', 'percentual']

export default function RelatorioOperacional({ tipo, fabricas, vendedores }) {
  const [fabrica, setFabrica] = useEstadoPagina(`relatorios.${tipo}.fabrica`, '')
  const [vendedor, setVendedor] = useEstadoPagina(`relatorios.${tipo}.vendedor`, '')
  const [rede, setRede] = useEstadoPagina(`relatorios.${tipo}.rede`, '')
  const [inicio, setInicio] = useEstadoPagina(`relatorios.${tipo}.inicio`, tipo === 'reativacoes' ? DATA_IMPLANTACAO : diasAtras(29))
  const [fim, setFim] = useEstadoPagina(`relatorios.${tipo}.fim`, dataLocal())
  const [status, setStatus] = useEstadoPagina(`relatorios.${tipo}.status`, '')
  const [incluirSemCompra, setIncluirSemCompra] = useEstadoPagina(`relatorios.${tipo}.incluirSemCompra`, false)
  const [codigo, setCodigo] = useEstadoPagina(`relatorios.${tipo}.codigo`, '')
  const [buscaCodigo, setBuscaCodigo] = useEstadoPagina(`relatorios.${tipo}.buscaCodigo`, '')
  const [escopo, setEscopo] = useEstadoPagina(`relatorios.${tipo}.escopo`, 'cliente')
  const [pagina, setPagina] = useEstadoPagina(`relatorios.${tipo}.pagina`, 1)
  const download = useAcao()
  const baixando = download.executando
  const redes = useDados('/relatorios/redes')
  const posicao = ehRelatorioDePosicao(tipo)
  const parametros = {
    inicio: posicao ? fim : inicio, fim, fabrica_id: fabrica, vendedor_id: vendedor, rede, status, codigo,
    incluir_sem_compra: tipo === 'mapa' && incluirSemCompra ? 'true' : null,
    escopo: tipo === 'reativacoes' ? escopo : null,
  }
  const valido = fim && fim <= dataLocal() && (posicao || inicio && inicio <= fim)
  const base = `/analises/relatorios/${tipo}`
  const resposta = useDados(valido ? montarCaminho(base, { ...parametros, pagina, limite: TAMANHO_PAGINA.relatorios }) : null)
  useRolagemPagina(`relatorio:${tipo}`, !!resposta.dados)
  function mudar(definir, valor) { definir(valor); setPagina(1); download.definirErro('') }
  const opcoesRede = (redes.dados || []).map((r) => ({ id: r.nome, nome: r.nome }))
  const opcoesSituacao = ['Ativo', 'Inativo', ...(incluirSemCompra ? ['Sem compra'] : [])].map((s) => ({ id: s, nome: s }))
  return <Cartao titulo={tiposRelatorio[tipo]}>
    <div className="filtros-comerciais faixa-filtros">
      {!posicao && <label>Data inicial<input type="date" value={inicio} max={fim} disabled={baixando} onChange={(e) => mudar(setInicio, e.target.value)} /></label>}
      <label>{posicao ? 'Posição em' : 'Data final'}<input type="date" value={fim} max={dataLocal()} disabled={baixando} onChange={(e) => mudar(setFim, e.target.value)} /></label>
      <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} disabled={baixando} aoMudar={(v) => mudar(setFabrica, v)} />
      <Seletor rotulo="Vendedor" todos="Toda a equipe" opcoes={vendedores} valor={vendedor} disabled={baixando} aoMudar={(v) => mudar(setVendedor, v)} />
      <Seletor rotulo="Rede" todos="Todas as redes" opcoes={opcoesRede} valor={rede} disabled={baixando} aoMudar={(v) => mudar(setRede, v)} />
      {tipo === 'mapa' && <Seletor rotulo="Situação" todos="Todas" opcoes={opcoesSituacao} valor={status} disabled={baixando} aoMudar={(v) => mudar(setStatus, v)} />}
      {tipo === 'reativacoes' && <Seletor rotulo="Tipo de reativação" opcoes={tiposReativacao} valor={escopo} disabled={baixando} aoMudar={(v) => mudar(setEscopo, v)} />}
    </div>
    {tipo === 'mapa' && <label className="opcao-rede"><input type="checkbox" checked={incluirSemCompra} disabled={baixando} onChange={(e) => { mudar(setIncluirSemCompra, e.target.checked); if (!e.target.checked && status === 'Sem compra') setStatus('') }} /> Incluir fábricas em que o cliente nunca comprou</label>}
    {tipo === 'reativacoes' && <div className="nota-painel">
      <p>Este relatório acompanha quem voltou a comprar após pelo menos 90 dias sem compra. O período seleciona a data desse retorno.</p>
      <p><strong>Nº pedido de retorno</strong> identifica o pedido da volta. <strong>Valor do retorno</strong> mostra quanto ele comprou nesse pedido. <strong>Qtde. após retorno</strong> conta os pedidos seguintes e <strong>Valor após retorno</strong> soma somente essas compras seguintes.</p>
    </div>}
    {tipo === 'precos' && <form className="filtros-comerciais" onSubmit={(e) => { e.preventDefault(); mudar(setCodigo, buscaCodigo.trim()) }}><label>Código exato<input value={buscaCodigo} onChange={(e) => setBuscaCodigo(e.target.value)} placeholder="Todos os códigos" /></label><button className="botao-secundario" disabled={baixando}>Filtrar código</button></form>}
    {!valido && <p role="alert">Informe datas válidas, com data final até hoje.</p>}
    <EstadoConsulta carregando={resposta.carregando || redes.carregando} erro={download.erro || resposta.erro || redes.erro}
      aoTentar={() => { download.definirErro(''); resposta.tentarNovamente(); redes.tentarNovamente() }} />
    {resposta.dados && <>
      <div className="filtros-comerciais"><p>{resposta.dados.total} registros encontrados.</p>
        <button className="botao-secundario" disabled={baixando}
          onClick={() => download.executar(() => baixarArquivo(montarCaminho(`${base}/pdf`, parametros), `relatorio-${tipo}.pdf`, { tempoLimite: 180000 }))}>
          {baixando ? 'Gerando PDF…' : 'Baixar PDF completo'}
        </button>
      </div>
      <Tabela colunas={resposta.dados.colunas.map((c) => c.titulo)}>
        {resposta.dados.linhas.map((linha, i) => <tr key={i}>{resposta.dados.colunas.map((c) => <td key={c.chave} className={formatosNumericos.includes(c.formato) ? 'valor-numerico' : undefined}>{formatarValor(linha[c.chave], c.formato)}</td>)}</tr>)}
      </Tabela>
      {!resposta.dados.total && <p>Nenhum registro com os filtros selecionados.</p>}
      <Paginacao pagina={pagina} total={resposta.dados.total} tamanho={TAMANHO_PAGINA.relatorios} aoMudar={setPagina} unidade="registros" carregando={resposta.carregando} />
      {resposta.dados.notas.map((nota) => <p className="nota-painel" key={nota}>{nota}</p>)}
    </>}
  </Cartao>
}
