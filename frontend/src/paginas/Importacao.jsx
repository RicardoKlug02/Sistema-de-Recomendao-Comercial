import { useRef, useState } from 'react'
import Cartao from '../componentes/Cartao'
import useDados from '../servicos/useDados'
import { importarArquivos } from '../servicos/importacao'
import './Importacao.css'

export default function Importacao({ usuario, aoImportar }) {
  const [cabecalho, definirCabecalho] = useState(null)
  const [itens, definirItens] = useState(null)
  const [erro, definirErro] = useState('')
  const [resultado, definirResultado] = useState(null)
  const [conferencia, definirConferencia] = useState(null)
  const [confirmado, definirConfirmado] = useState(false)
  const [enviando, definirEnviando] = useState(false)
  const [versao, definirVersao] = useState(0)
  const pendente = useRef(false)
  const historico = useDados('/cargas/historico', versao)
  const podeImportar = ['admin', 'gestor'].includes(usuario.perfil)
  async function importar(e) {
    e.preventDefault()
    if (pendente.current) return
    pendente.current = true; definirEnviando(true); definirErro(''); definirResultado(null)
    try {
      if (conferencia) {
        if (!confirmado) throw new Error('Confirme que os arquivos contêm somente vendas que geram comissão.')
        definirResultado(await importarArquivos(cabecalho, itens, conferencia.token_conferencia))
        definirConferencia(null); definirConfirmado(false)
        definirVersao((v) => v + 1)
        aoImportar()
      } else definirConferencia(await importarArquivos(cabecalho, itens))
    } catch (falha) { definirErro(falha.message); definirConferencia(null); definirConfirmado(false) }
    finally { pendente.current = false; definirEnviando(false) }
  }
  return <main className="conteudo-painel tela-importacao">
    <header className="cabecalho-painel"><div><h1>Importação de dados</h1><p>Envie duas planilhas do mesmo período: um mês ou vários meses juntos. Somente vendas efetivadas que geram comissão.</p></div></header>
    <Cartao titulo="Importar planilhas">
      {podeImportar ? <form onSubmit={importar} className="formulario-carga">
        <label>1. Cabeçalhos dos pedidos<input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={(e) => { definirCabecalho(e.target.files[0]); definirConferencia(null); definirConfirmado(false); definirResultado(null) }} /></label>
        <label>2. Itens vendidos<input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={(e) => { definirItens(e.target.files[0]); definirConferencia(null); definirConfirmado(false); definirResultado(null) }} /></label>
        <p>Pedidos fechados diretamente pela fábrica podem não ter itens. Eles entram normalmente no faturamento.</p>
        {conferencia && <section aria-label="Conferência da importação">
          <h2>Confira antes de importar</h2>
          <p>Período: {conferencia.inicio} a {conferencia.fim}. Valor total dos arquivos: {conferencia.valor_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}.</p>
          <p>{conferencia.processados} pedidos: {conferencia.adicionados} novos, {conferencia.atualizados} atualizações e {conferencia.itens} linhas de itens. {conferencia.pedidos_sem_itens} pedidos sem itens nesta carga.</p>
          {conferencia.avisos.map((aviso) => <p key={aviso}>{aviso}</p>)}
          <div className="rolagem-tabela"><table><thead><tr><th>Pedido</th><th>Cliente</th><th>Fábrica</th><th>Data</th><th>Valor</th><th>Ação</th></tr></thead>
            <tbody>{conferencia.pedidos.map((p) => <tr key={`${p.fabrica}:${p.pedido}`}><td>{p.pedido}</td><td>{p.cliente}</td><td>{p.fabrica}</td><td>{p.data}</td><td>{p.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td><td>{p.acao}</td></tr>)}</tbody></table></div>
          {conferencia.processados > 100 && <p>A tabela mostra os primeiros 100 pedidos. Os totais incluem todos os pedidos.</p>}
          <label><input type="checkbox" checked={confirmado} disabled={enviando} onChange={(e) => definirConfirmado(e.target.checked)} />Confirmo que as planilhas contêm somente vendas efetivadas que geram comissão.</label>
        </section>}
        <button className="botao-principal" disabled={enviando || !cabecalho || !itens || (conferencia && !confirmado)}>{enviando ? 'Processando planilhas…' : conferencia ? 'Confirmar importação' : 'Conferir planilhas'}</button>
      </form> : <p>A importação é permitida ao administrador ou gestor.</p>}
      {erro && <p className="erro-campo" role="alert">{erro}</p>}
      {resultado && <div role="status"><p>{resultado.processados} pedidos: {resultado.adicionados} novos e {resultado.atualizados} atualizados; {resultado.itens} itens importados.</p>
        {resultado.avisos.map((aviso) => <p key={aviso}>{aviso}</p>)}</div>}
    </Cartao>
    <Cartao titulo="Histórico de importações">
      {historico.erro && <p role="alert">{historico.erro}</p>}
      {historico.carregando ? <p role="status">Carregando histórico…</p> : <div className="rolagem-tabela"><table>
        <thead><tr><th>Pedidos</th><th>Itens</th><th>Data</th><th>Usuário</th><th>Pedidos processados</th></tr></thead>
        <tbody>{historico.dados?.map((h) => <tr key={h.id}><td>{h.arquivo}</td><td>{h.arquivo_itens}</td><td>{h.data}</td><td>{h.usuario}</td><td>{h.processados}</td></tr>)}</tbody>
      </table>{historico.dados?.length === 0 && <p>Nenhuma importação realizada.</p>}</div>}
    </Cartao>
  </main>
}
