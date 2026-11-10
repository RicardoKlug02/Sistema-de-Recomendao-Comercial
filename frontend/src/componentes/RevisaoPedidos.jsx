import { useState } from 'react'
import useDados from '../hooks/useDados'
import { solicitar } from '../servicos/api'
import { formatarData, formatarDataHora, formatarMoeda } from '../servicos/formatacao'
import EstadoConsulta from './EstadoConsulta'
import Paginacao from './Paginacao'

const nomes = { NAO_REVISADO: 'Pendente de revisão', VENDA_DIRETA: 'Venda direta confirmada',
  VENDA_COM_ITENS: 'Venda com itens', AJUSTE_COMISSIONADO: 'Ajuste comissionado — valor sem nova compra',
  BONIFICACAO: 'Bonificação — fora das análises', DUPLICIDADE: 'Duplicidade — fora das análises', OUTRO_TIPO: 'Outro tipo — fora das análises' }

function Decisao({ pedido, aoSalvar }) {
  const [classificacao, setClassificacao] = useState(pedido.classificacao)
  const [motivo, setMotivo] = useState('')
  const [evidencia, setEvidencia] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const historico = useDados(`/cargas/pedidos/${pedido.id}/historico`)
  async function salvar(e) {
    e.preventDefault(); setSalvando(true); setErro('')
    try {
      await solicitar(`/cargas/pedidos/${pedido.id}/revisao`, { method: 'POST',
        body: { classificacao, motivo, evidencia, versao: pedido.versao } })
      aoSalvar()
    } catch (falha) { setErro(falha.message) }
    finally { setSalvando(false) }
  }
  return <form onSubmit={salvar}>
    <div className="filtros-comerciais">
      <label>Classificação<select value={classificacao} disabled={salvando} onChange={(e) => setClassificacao(e.target.value)}>
        {Object.entries(nomes).map(([id, nome]) => <option key={id} value={id}>{nome}</option>)}
      </select></label>
      <label>Motivo da decisão<input required minLength={5} maxLength={1000} value={motivo} disabled={salvando} onChange={(e) => setMotivo(e.target.value)} /></label>
      <label>Referência da conferência<input required={classificacao === 'VENDA_DIRETA'} minLength={classificacao === 'VENDA_DIRETA' ? 5 : undefined} maxLength={1000}
        placeholder="Pedido da fábrica, documento ou contato responsável" value={evidencia} disabled={salvando} onChange={(e) => setEvidencia(e.target.value)} /></label>
      <button className="botao-secundario" disabled={salvando}>{salvando ? 'Salvando…' : 'Salvar revisão'}</button>
    </div>
    <p>Bonificação, duplicidade e outros tipos saem das análises. Ajuste comissionado entra somente nos valores: não conta como novo pedido de compra, não reinicia a inatividade e não altera o histórico de produtos. O registro original é preservado. Venda direta confirmada conta como compra, mas não confirma quais produtos foram comprados.</p>
    {erro && <p role="alert">{erro}</p>}
    <EstadoConsulta erro={historico.erro} carregando={historico.carregando} aoTentar={historico.tentarNovamente} />
    {historico.dados?.map((h) => <p key={h.id}>{formatarDataHora(h.data)} · {h.usuario} · {nomes[h.classificacao]}: {h.motivo}{h.evidencia ? ` · Referência: ${h.evidencia}` : ''}</p>)}
  </form>
}

export default function RevisaoPedidos({ aoAlterar }) {
  const [classificacao, setClassificacao] = useState('NAO_REVISADO')
  const [busca, setBusca] = useState('')
  const [pedido, setPedido] = useState('')
  const [semItens, setSemItens] = useState(true)
  const [pagina, setPagina] = useState(1)
  const [aberto, setAberto] = useState(null)
  const [sucesso, setSucesso] = useState('')
  const [versao, setVersao] = useState(0)
  const params = new URLSearchParams({ classificacao, pedido, somente_sem_itens: semItens, pagina })
  const consulta = useDados(`/cargas/pedidos?${params}`, versao)
  function atualizar(setter, valor) { setter(valor); setPagina(1); setAberto(null); setSucesso('') }
  function salvo() { setVersao(v => v+1); setAberto(null); setSucesso('Revisão salva. As análises usarão a nova classificação.'); aoAlterar?.() }
  return <section aria-label="Revisão de pedidos importados">
    <h2>Revisão de pedidos importados</h2>
    <p>Sem itens não significa venda direta. Confira o relatório original e registre a decisão. Pedidos pendentes continuam nos totais e geram aviso de dados incompletos até serem revisados.</p>
    <form className="filtros-comerciais" onSubmit={(e) => { e.preventDefault(); atualizar(setPedido, busca.trim()) }}>
      <label>Número do pedido<input value={busca} onChange={(e) => setBusca(e.target.value)} /></label>
      <label>Situação da revisão<select value={classificacao} onChange={(e) => atualizar(setClassificacao,e.target.value)}>
        <option value="">Todas as classificações</option>{Object.entries(nomes).map(([id,nome]) => <option key={id} value={id}>{nome}</option>)}
      </select></label>
      <label><input type="checkbox" checked={semItens} onChange={(e) => atualizar(setSemItens,e.target.checked)} /> Somente pedidos sem itens</label>
      <button className="botao-secundario">Buscar pedido</button>
    </form>
    {sucesso && <p role="status">{sucesso}</p>}
    <EstadoConsulta erro={consulta.erro} carregando={consulta.carregando} aoTentar={consulta.tentarNovamente} />
    {consulta.dados?.itens.map((p) => <article key={p.id} className="nota-painel">
      <p><strong>Pedido {p.pedido} · {p.fabrica}</strong> · {formatarData(p.data)} · {formatarMoeda(p.valor)}</p>
      <p>{p.cliente} · CNPJ/CPF {p.cnpj_cpf || 'Não informado'} · Rede: {p.rede || 'Sem rede cadastrada'}</p>
      <p>{nomes[p.classificacao]} · {p.considerar_analises ? 'Incluído nas análises' : 'Desconsiderado nas análises'}</p>
      <button type="button" className="botao-texto" onClick={() => setAberto(aberto === p.id ? null : p.id)}>Revisar e ver histórico do pedido {p.pedido}</button>
      {aberto === p.id && <Decisao key={`${p.id}:${p.versao}`} pedido={p} aoSalvar={salvo} />}
    </article>)}
    {consulta.dados && <Paginacao pagina={pagina} total={consulta.dados.total} tamanho={25} aoMudar={(p) => { setPagina(p); setAberto(null) }} unidade="pedidos" carregando={consulta.carregando} />}
    {consulta.dados?.total === 0 && <p>Nenhum pedido encontrado com esses filtros.</p>}
  </section>
}
