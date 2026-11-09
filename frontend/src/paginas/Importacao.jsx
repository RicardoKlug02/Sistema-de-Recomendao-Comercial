import { useId, useState } from 'react'
import Cartao from '../componentes/Cartao'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Pagina from '../componentes/Pagina'
import Tabela from '../componentes/Tabela'
import useAcao from '../hooks/useAcao'
import useDados from '../hooks/useDados'
import { dataLocal, formatarData, formatarMoeda } from '../servicos/formatacao'
import { conferirPlanilhas, confirmarImportacao } from '../servicos/importacao'

export default function Importacao({ aoImportar }) {
  const confirmacaoId = useId()
  const [cabecalho, definirCabecalho] = useState(null)
  const [itens, definirItens] = useState(null)
  const [resultado, definirResultado] = useState(null)
  const [conferencia, definirConferencia] = useState(null)
  const [confirmado, definirConfirmado] = useState(false)
  const [versao, definirVersao] = useState(0)
  const [modo, definirModo] = useState('atualizar')
  const [mes, definirMes] = useState('')
  const envio = useAcao()
  const enviando = envio.executando
  const historico = useDados('/cargas/historico', versao)

  function descartarConferencia() { definirConferencia(null); definirConfirmado(false) }
  const selecionarArquivo = (definir) => (e) => { definir(e.target.files[0]); descartarConferencia(); definirResultado(null) }

  async function importar(e) {
    e.preventDefault()
    definirResultado(null)
    const escopo = { modo, mes }
    const concluiu = await envio.executar(async () => {
      if (!conferencia) {
        definirConferencia(await conferirPlanilhas(cabecalho, itens, escopo))
        return
      }
      definirResultado(await confirmarImportacao(cabecalho, itens, conferencia.token_conferencia, escopo))
      descartarConferencia()
      definirVersao((v) => v + 1)
      aoImportar()
    })
    if (!concluiu) descartarConferencia()
  }

  return (
    <Pagina titulo="Importação de dados" descricao="Confira suas planilhas e mantenha o histórico comercial atualizado." className="tela-importacao">
      <Cartao titulo="Importar planilhas">
        <form onSubmit={importar} className="formulario-carga">
          <label>
            Modo de importação
            <select value={modo} disabled={enviando} onChange={(e) => {
              definirModo(e.target.value); descartarConferencia(); definirResultado(null)
            }}>
              <option value="atualizar">Atualizar pedidos informados</option>
              <option value="sincronizar_mes">Sincronizar mês completo</option>
            </select>
          </label>
          {modo === 'sincronizar_mes' ? <>
            <label>Mês a sincronizar<input type="month" required value={mes} max={dataLocal().slice(0, 7)} disabled={enviando}
              onChange={(e) => { definirMes(e.target.value); descartarConferencia(); definirResultado(null) }} /></label>
            <p>Envie todas as vendas do mês, de todos os vendedores e fábricas. A conferência mostrará os pedidos ausentes que serão excluídos e os itens removidos. Outros meses serão preservados.</p>
          </> : <p>Atualiza os pedidos enviados. Pedidos ausentes e itens de pedidos que vierem sem detalhamento são conservados. Para refletir exclusões, use Sincronizar mês completo.</p>}
          <label>
            1. Cabeçalhos dos pedidos
            <input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={selecionarArquivo(definirCabecalho)} />
          </label>
          <label>
            2. Itens vendidos
            <input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={selecionarArquivo(definirItens)} />
          </label>
          <p>Pedidos fechados diretamente pela fábrica podem não ter itens. Eles entram normalmente no faturamento.</p>
          {conferencia && (
            <section aria-label="Conferência da importação">
              <h2>Confira antes de importar</h2>
              <p>Período: {conferencia.inicio} a {conferencia.fim}. Valor total dos arquivos: {formatarMoeda(conferencia.valor_total)}.</p>
              <p>
                {conferencia.processados} pedidos: {conferencia.adicionados} novos, {conferencia.atualizados} atualizações
                e {conferencia.itens} linhas de itens. {conferencia.pedidos_sem_itens} pedidos sem itens nesta carga.
              </p>
              <p>{conferencia.excluidos ?? 0} pedidos serão excluídos; {conferencia.itens_removidos ?? 0} linhas de itens serão removidas; {conferencia.quantidades_reduzidas ?? 0} produtos terão quantidade reduzida.</p>
              {conferencia.avisos.map((aviso) => <p key={aviso}>{aviso}</p>)}
              <Tabela colunas={['Pedido', 'Cliente', 'Fábrica', 'Data', 'Valor', 'Ação']}>
                {conferencia.pedidos.map((p) => (
                  <tr key={`${p.fabrica}:${p.pedido}`}><td>{p.pedido}</td><td>{p.cliente}</td><td>{p.fabrica}</td><td>{p.data}</td><td>{formatarMoeda(p.valor)}</td><td>{p.acao}</td></tr>
                ))}
              </Tabela>
              {conferencia.pedidos_excluidos?.length > 0 && <>
                <h3>Pedidos que serão excluídos</h3>
                <p>Valor dos pedidos ausentes: {formatarMoeda(conferencia.valor_excluido)}.</p>
                <Tabela colunas={['Pedido', 'Fábrica', 'Data', 'Valor', 'Itens']}>
                  {conferencia.pedidos_excluidos.map((p) => <tr key={`${p.fabrica}:${p.pedido}`}>
                    <td>{p.pedido}</td><td>{p.fabrica}</td><td>{formatarData(p.data)}</td><td>{formatarMoeda(p.valor)}</td><td>{p.itens}</td>
                  </tr>)}
                </Tabela>
                {conferencia.excluidos > 100 && <p>A lista mostra os primeiros 100 pedidos a excluir. Os totais incluem todos.</p>}
              </>}
              {conferencia.processados > 100 && <p>A tabela mostra os primeiros 100 pedidos. Os totais incluem todos os pedidos.</p>}
              <div className="confirmacao-carga">
                <input id={confirmacaoId} type="checkbox" checked={confirmado} disabled={enviando} onChange={(e) => definirConfirmado(e.target.checked)} />
                <label htmlFor={confirmacaoId}>{modo === 'sincronizar_mes'
                  ? `Confirmo que as planilhas contêm todas as vendas efetivadas que geram comissão do mês ${mes}, de toda a equipe e de todas as fábricas, e autorizo as exclusões e substituições mostradas na conferência.`
                  : 'Confirmo que as planilhas contêm somente vendas efetivadas que geram comissão.'}</label>
              </div>
            </section>
          )}
          <button className="botao-principal" disabled={enviando || !cabecalho || !itens || (conferencia && !confirmado)}>
            {enviando ? 'Processando planilhas…' : conferencia ? 'Confirmar importação' : 'Conferir planilhas'}
          </button>
        </form>
        {envio.erro && <p className="erro-campo" role="alert">{envio.erro}</p>}
        {resultado && (
          <div role="status">
            <p>{resultado.processados} pedidos: {resultado.adicionados} novos e {resultado.atualizados} atualizados; {resultado.itens} itens importados.</p>
            {resultado.modo === 'sincronizar_mes' && <p>Mês {resultado.mes} sincronizado: {resultado.excluidos} pedidos excluídos, {resultado.itens_removidos} linhas de itens removidas e {resultado.quantidades_reduzidas} produtos com quantidade reduzida.</p>}
            {resultado.avisos.map((aviso) => <p key={aviso}>{aviso}</p>)}
          </div>
        )}
      </Cartao>
      <Cartao titulo="Histórico de importações">
        <EstadoConsulta carregando={historico.carregando} erro={historico.erro} aoTentar={historico.tentarNovamente}
          vazio={historico.dados?.length === 0} mensagem="Nenhuma importação realizada." />
        {historico.dados?.length > 0 && (
          <Tabela colunas={['Pedidos', 'Itens', 'Data', 'Usuário', 'Pedidos processados', 'Operação']}>
            {historico.dados.map((h) => (
              <tr key={h.id}><td>{h.arquivo}</td><td>{h.arquivo_itens}</td><td>{h.data}</td><td>{h.usuario}</td><td>{h.processados}</td>
                <td>{h.modo === 'sincronizar_mes' ? `Mês ${h.mes}: ${h.excluidos} pedidos excluídos, ${h.itens_removidos} itens removidos` : 'Atualização dos pedidos informados'}</td></tr>
            ))}
          </Tabela>
        )}
      </Cartao>
    </Pagina>
  )
}
