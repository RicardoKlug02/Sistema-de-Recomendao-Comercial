import { useState } from 'react'
import { solicitar } from '../servicos/api'
import useDados from '../servicos/useDados'
import { dataLocal, formatarData, formatarDataHora } from '../servicos/datas'
import EstadoConsulta from './comercial/EstadoConsulta'
import { situacoesAcompanhamento } from '../servicos/acompanhamento'

export default function AcompanhamentoAlerta({ grupo, aoSalvar }) {
  const atual = grupo.acompanhamento || { situacao: 'PENDENTE', versao: 0 }
  const [situacao, setSituacao] = useState(atual.situacao)
  const [motivo, setMotivo] = useState(atual.motivo || '')
  const [data, setData] = useState(atual.proximo_contato || '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [verHistorico, setVerHistorico] = useState(false)
  const historico = useDados(verHistorico ? `/comercial/alertas/${grupo.cliente_id}/historico` : null)
  const permiteData = ['CONTATADO', 'AGUARDANDO_RETORNO'].includes(situacao)
  async function salvar(e) {
    e.preventDefault(); setSalvando(true); setErro('')
    try {
      await solicitar(`/comercial/alertas/${grupo.cliente_id}/acompanhamento`, { method: 'POST', body: {
        situacao, motivo, proximo_contato: permiteData && data ? data : null, versao: atual.versao, assinatura: grupo.assinatura,
      } })
      aoSalvar()
    } catch (falha) { setErro(falha.message) }
    finally { setSalvando(false) }
  }
  return <section className="acompanhamento-alerta" aria-label={`Acompanhamento de ${grupo.cliente}`}>
    <p><strong>Acompanhamento: {situacoesAcompanhamento[atual.situacao]}</strong></p>
    {atual.novos_sinais && <p role="status">Os sinais mudaram desde o último acompanhamento. Revise os próximos passos.</p>}
    {atual.proximo_contato && <p>Próximo contato: {formatarData(atual.proximo_contato)}{atual.proximo_contato < dataLocal() && ' · Data vencida'}</p>}
    {atual.usuario && <p>Último registro por {atual.usuario} em {formatarDataHora(atual.atualizado_em)}.</p>}
    <details><summary>Registrar acompanhamento</summary>
      <p>Compartilhado com a equipe. O registro não elimina os sinais calculados.</p>
      <form onSubmit={salvar}>
        <fieldset disabled={salvando}>
          <label>Situação<select aria-label="Situação do acompanhamento" value={situacao} onChange={(e) => setSituacao(e.target.value)}>{Object.entries(situacoesAcompanhamento).map(([id, nome]) => <option value={id} key={id}>{nome}</option>)}</select></label>
          <label>Motivo ou observação<textarea required={situacao === 'DISPENSADO'} maxLength={1000} value={motivo} onChange={(e) => setMotivo(e.target.value)} /></label>
          {permiteData && <label>Próxima data de contato<input type="date" min={dataLocal()} required={situacao === 'AGUARDANDO_RETORNO'} value={data} onChange={(e) => setData(e.target.value)} /></label>}
          <button className="botao-secundario" type="submit">{salvando ? 'Salvando…' : 'Salvar acompanhamento'}</button>
        </fieldset>
      </form>
      {erro && <p role="alert">{erro}</p>}
    </details>
    <details onToggle={(e) => setVerHistorico(e.currentTarget.open)}><summary>Histórico de acompanhamento</summary>
      <EstadoConsulta carregando={historico.carregando} erro={historico.erro} aoTentar={historico.tentarNovamente} />
      {historico.dados?.length === 0 && <p>Nenhum acompanhamento registrado.</p>}
      <p>Até 30 registros mais recentes.</p>
      <ol>{historico.dados?.map((a) => <li key={a.versao}><strong>{situacoesAcompanhamento[a.situacao]}</strong> · {a.usuario} · {formatarDataHora(a.atualizado_em)}
        {a.motivo && <p>{a.motivo}</p>}{a.proximo_contato && <p>Contato previsto: {formatarData(a.proximo_contato)}</p>}</li>)}</ol>
    </details>
  </section>
}
