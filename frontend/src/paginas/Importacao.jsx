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
      definirResultado(await importarArquivos(cabecalho, itens))
      definirVersao((v) => v + 1)
      aoImportar()
    } catch (falha) { definirErro(falha.message) }
    finally { pendente.current = false; definirEnviando(false) }
  }
  return <main className="conteudo-painel tela-importacao">
    <header className="cabecalho-painel"><div><h1>Importação de dados</h1><p>Envie os pedidos e os itens do mesmo período.</p></div></header>
    <Cartao titulo="Importar planilhas">
      {podeImportar ? <form onSubmit={importar} className="formulario-carga">
        <label>1. Cabeçalhos dos pedidos<input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={(e) => definirCabecalho(e.target.files[0])} /></label>
        <label>2. Itens vendidos<input type="file" accept=".xls,.xlsx" required disabled={enviando} onChange={(e) => definirItens(e.target.files[0])} /></label>
        <p>Pedidos fechados diretamente pela fábrica podem não ter itens. Eles entram normalmente no faturamento.</p>
        <button className="botao-principal" disabled={enviando || !cabecalho || !itens}>{enviando ? 'Processando planilhas…' : 'Importar os dois arquivos'}</button>
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
