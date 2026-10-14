import { useState } from 'react'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import FiltroFabrica from '../componentes/comercial/FiltroFabrica'
import Paginacao from '../componentes/comercial/Paginacao'
import Cartao from '../componentes/Cartao'
import useDados from '../servicos/useDados'
import { solicitar } from '../servicos/api'
import { formatarMoeda } from '../servicos/dadosPainel'
import { dataLocal, diasAtras, formatarData } from '../servicos/datas'
import RelatorioRede from './RelatorioRede'

const tipos = { rede: 'Códigos comprados pela rede', mapa: 'Mapa cliente x fábrica', reativacoes: 'Resultado das reativações', inativos: 'Clientes inativos', precos: 'Evolução dos preços por código', regioes: 'Regiões imediatas por vendedor' }
function valorCelula(valor, formato) {
  if (valor === null || valor === undefined) return formato === 'percentual' ? 'Sem base' : '—'
  if (formato === 'moeda') return formatarMoeda(valor)
  if (formato === 'data') return formatarData(valor)
  if (formato === 'percentual') return `${valor > 0 ? '+' : ''}${valor.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
  if (formato === 'numero') return valor.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
  return valor
}

function RelatorioOperacional({ tipo, fabricas, vendedores }) {
  const [fabrica, setFabrica] = useState('')
  const [vendedor, setVendedor] = useState('')
  const [rede, setRede] = useState('')
  const [inicio, setInicio] = useState(tipo === 'reativacoes' ? '2026-09-29' : diasAtras(29))
  const [fim, setFim] = useState(dataLocal())
  const [status, setStatus] = useState('')
  const [incluirSemCompra, setIncluirSemCompra] = useState(false)
  const [codigo, setCodigo] = useState('')
  const [buscaCodigo, setBuscaCodigo] = useState('')
  const [escopo, setEscopo] = useState('cliente')
  const [pagina, setPagina] = useState(1)
  const [baixando, setBaixando] = useState(false)
  const [erro, setErro] = useState('')
  const redes = useDados('/relatorios/redes')
  const posicao = ['mapa', 'inativos'].includes(tipo)
  const parametros = new URLSearchParams({ inicio: posicao ? fim : inicio, fim })
  if (fabrica) parametros.set('fabrica_id', fabrica)
  if (vendedor) parametros.set('vendedor_id', vendedor)
  if (rede) parametros.set('rede', rede)
  if (status) parametros.set('status', status)
  if (tipo === 'mapa' && incluirSemCompra) parametros.set('incluir_sem_compra', 'true')
  if (codigo) parametros.set('codigo', codigo)
  if (tipo === 'reativacoes') parametros.set('escopo', escopo)
  const valido = fim && fim <= dataLocal() && (posicao || inicio && inicio <= fim)
  const base = `/analises/relatorios/${tipo}`
  const resposta = useDados(valido ? `${base}?${parametros}&pagina=${pagina}` : null)
  function mudar(setter, valor) { setter(valor); setPagina(1); setErro('') }
  async function baixar() {
    setBaixando(true); setErro('')
    try {
      const pdf = await solicitar(`${base}/pdf?${parametros}`, { formato: 'blob', tempoLimite: 180000 })
      const url = URL.createObjectURL(pdf)
      const a = document.createElement('a'); a.href = url; a.download = `relatorio-${tipo}.pdf`
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (falha) { setErro(falha.message) }
    finally { setBaixando(false) }
  }
  return <Cartao titulo={tipos[tipo]}>
    <div className="filtros-comerciais faixa-filtros">
      {!posicao && <label>Data inicial<input type="date" value={inicio} max={fim} disabled={baixando} onChange={(e) => mudar(setInicio, e.target.value)} /></label>}
      <label>{posicao ? 'Posição em' : 'Data final'}<input type="date" value={fim} max={dataLocal()} disabled={baixando} onChange={(e) => mudar(setFim, e.target.value)} /></label>
      <FiltroFabrica fabricas={fabricas} valor={fabrica} disabled={baixando} aoMudar={(v) => mudar(setFabrica, v)} />
      <label>Vendedor<select aria-label="Vendedor" value={vendedor} disabled={baixando} onChange={(e) => mudar(setVendedor, e.target.value)}><option value="">Toda a equipe</option>{vendedores.map((v) => <option key={v.id} value={v.id}>{v.nome}</option>)}</select></label>
      <label>Rede<select aria-label="Rede" value={rede} disabled={baixando} onChange={(e) => mudar(setRede, e.target.value)}><option value="">Todas as redes</option>{redes.dados?.map((r) => <option key={r.nome}>{r.nome}</option>)}</select></label>
      {tipo === 'mapa' && <label>Situação<select value={status} aria-label="Situação" disabled={baixando} onChange={(e) => mudar(setStatus, e.target.value)}><option value="">Todas</option>{['Ativo', 'Inativo', ...(incluirSemCompra ? ['Sem compra'] : [])].map((s) => <option key={s}>{s}</option>)}</select></label>}
      {tipo === 'reativacoes' && <label>Tipo de reativação<select aria-label="Tipo de reativação" value={escopo} disabled={baixando} onChange={(e) => mudar(setEscopo, e.target.value)}><option value="cliente">Cliente no escritório</option><option value="fabrica">Cliente x fábrica</option></select></label>}
    </div>
    {tipo === 'mapa' && <label className="opcao-rede"><input type="checkbox" checked={incluirSemCompra} disabled={baixando} onChange={(e) => { mudar(setIncluirSemCompra, e.target.checked); if (!e.target.checked && status === 'Sem compra') setStatus('') }} /> Incluir fábricas em que o cliente nunca comprou</label>}
    {tipo === 'reativacoes' && <div className="nota-painel">
      <p>Este relatório acompanha quem voltou a comprar após pelo menos 90 dias sem compra. O período seleciona a data desse retorno.</p>
      <p><strong>Nº pedido de retorno</strong> identifica o pedido da volta. <strong>Valor do retorno</strong> mostra quanto ele comprou nesse pedido. <strong>Qtde. após retorno</strong> conta os pedidos seguintes e <strong>Valor após retorno</strong> soma somente essas compras seguintes.</p>
    </div>}
    {tipo === 'precos' && <form className="filtros-comerciais" onSubmit={(e) => { e.preventDefault(); mudar(setCodigo, buscaCodigo.trim()) }}><label>Código exato<input value={buscaCodigo} onChange={(e) => setBuscaCodigo(e.target.value)} placeholder="Todos os códigos" /></label><button className="botao-secundario" disabled={baixando}>Filtrar código</button></form>}
    {!valido && <p role="alert">Informe datas válidas, com data final até hoje.</p>}
    <EstadoConsulta carregando={resposta.carregando || redes.carregando} erro={erro || resposta.erro || redes.erro} />
    {resposta.dados && <>
      <div className="filtros-comerciais"><p>{resposta.dados.total} registros encontrados.</p><button className="botao-secundario" disabled={baixando} onClick={baixar}>{baixando ? 'Gerando PDF…' : 'Baixar PDF completo'}</button></div>
      <div className="rolagem-tabela"><table><thead><tr>{resposta.dados.colunas.map((c) => <th key={c.chave}>{c.titulo}</th>)}</tr></thead><tbody>{resposta.dados.linhas.map((r, i) => <tr key={i}>{resposta.dados.colunas.map((c) => <td key={c.chave}>{valorCelula(r[c.chave], c.formato)}</td>)}</tr>)}</tbody></table></div>
      {!resposta.dados.total && <p>Nenhum registro com os filtros selecionados.</p>}
      <Paginacao pagina={pagina} total={resposta.dados.total} tamanho={50} aoMudar={setPagina} unidade="registros" carregando={resposta.carregando} />
      {resposta.dados.notas.map((nota) => <p className="nota-painel" key={nota}>{nota}</p>)}
    </>}
  </Cartao>
}

export default function Relatorios({ fabricas = [], vendedores = [] }) {
  const [tipo, setTipo] = useState('rede')
  return <main className="conteudo-painel" id="conteudo">
    <CabecalhoPagina titulo="Relatórios" descricao="Carteira, recuperação, preços e regiões a partir do histórico importado." />
    <div className="filtros-comerciais faixa-filtros"><label>Relatório<select aria-label="Relatório" value={tipo} onChange={(e) => setTipo(e.target.value)}>{Object.entries(tipos).map(([id, nome]) => <option key={id} value={id}>{nome}</option>)}</select></label></div>
    {tipo === 'rede' ? <RelatorioRede fabricas={fabricas} /> : <RelatorioOperacional key={tipo} tipo={tipo} fabricas={fabricas} vendedores={vendedores} />}
  </main>
}