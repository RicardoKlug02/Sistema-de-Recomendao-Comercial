import { useRef, useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import { historicoInicial, importarArquivo, obterSituacao, validarArquivo } from '../servicos/importacao'
import './Importacao.css'

// Controla a seleção da planilha e exibe os resultados demonstrativos.
export default function Importacao({ usuario, ativa }) {
  const [arquivo, definirArquivo] = useState(null)
  const [erro, definirErro] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const [historico, definirHistorico] = useState(historicoInicial)
  const [resultado, definirResultado] = useState(null)
  const [pagina, definirPagina] = useState(1)
  const [detalhes, definirDetalhes] = useState(null)
  const campoArquivo = useRef(null)
  const dialogo = useRef(null)
  const envioEmCurso = useRef(false)
  const porPagina = 6
  const totalPaginas = Math.ceil(historico.length / porPagina)
  const inicio = (pagina - 1) * porPagina

  function selecionarArquivos(arquivos) {
    if (envioEmCurso.current || !arquivos.length) return
    if (arquivos.length !== 1) {
      definirErro('Selecione apenas uma planilha por vez.')
      return
    }
    const selecionado = arquivos[0]
    const mensagem = validarArquivo(selecionado)
    definirErro(mensagem)
    if (!mensagem) {
      definirArquivo(selecionado)
      definirResultado(null)
    }
  }

  async function importar() {
    if (envioEmCurso.current) return
    const mensagem = validarArquivo(arquivo)
    definirErro(mensagem)
    if (mensagem) return
    envioEmCurso.current = true
    definirEnviando(true)
    definirResultado(null)
    try {
      const retorno = await importarArquivo(arquivo, usuario)
      definirResultado(retorno)
      definirHistorico((itens) => [retorno, ...itens])
      definirPagina(1)
    } catch (falha) {
      definirErro(falha.message || 'Não foi possível importar. Tente novamente.')
    } finally {
      envioEmCurso.current = false
      definirEnviando(false)
    }
  }

  function abrirDetalhes(item) {
    definirDetalhes(item)
    dialogo.current.showModal()
  }

  return (
    <main className="conteudo-painel tela-importacao" hidden={!ativa}>
      <p className="caminho-importacao">Importação › Importar Dados</p>
      <header className="cabecalho-painel">
        <div><h1 id="titulo-importacao" tabIndex={-1}>Importação de Dados</h1><p>Atualize os dados comerciais por meio de uma planilha Excel.</p></div>
        <span className="aviso-demonstracao">Dados demonstrativos</span>
      </header>
      <Cartao titulo="Importar planilha" descricao="Envie dados de clientes, produtos e pedidos.">
        <div className="area-arquivo" onDragOver={(evento) => evento.preventDefault()}
          onDrop={(evento) => { evento.preventDefault(); selecionarArquivos(evento.dataTransfer.files) }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M12 16V4m-5 5 5-5 5 5M5 15v5h14v-5" /></svg>
          <strong>Arraste e solte o arquivo aqui</strong><span>ou</span>
          <button className="botao-secundario" disabled={enviando} onClick={() => campoArquivo.current.click()}>Selecionar arquivo</button>
          <small id="orientacao-arquivo">Formatos aceitos: XLS, XLSX — Tamanho máximo: 10 MB</small>
          <input ref={campoArquivo} type="file" accept=".xls,.xlsx" hidden disabled={enviando}
            aria-label="Selecionar planilha" aria-describedby="orientacao-arquivo"
            onChange={(evento) => { selecionarArquivos(evento.target.files); evento.target.value = '' }} />
        </div>
        {arquivo && <div className="arquivo-selecionado">
          <div><strong>{arquivo.name}</strong><small>{(arquivo.size / 1024 / 1024).toLocaleString('pt-BR', { maximumFractionDigits: 2 })} MB</small></div>
          <button className="botao-detalhes" disabled={enviando} onClick={() => campoArquivo.current.click()}>Substituir</button>
          <button className="botao-detalhes" disabled={enviando} onClick={() => { definirArquivo(null); definirErro(''); definirResultado(null) }}>Remover</button>
        </div>}
        {erro && <p className="erro-campo" role="alert">{erro}</p>}
        <button className="botao-principal botao-importar" disabled={!arquivo || enviando} onClick={importar}>{enviando ? 'Importando…' : 'Importar Dados'}</button>
        <p className="aviso-simulacao">Simulação: o conteúdo do arquivo não será lido nem enviado. Os resultados são exemplos.</p>
      </Cartao>
      <Cartao titulo="Status da Importação">
        <div role="status" aria-live="polite">
          {enviando ? <><p>Importando dados de demonstração…</p><progress aria-label="Importação em andamento" /></> : resultado ? <>
            <p><span className="etiqueta etiqueta-alerta">{obterSituacao(resultado)}</span></p>
            <progress value="100" max="100" aria-label="Importação concluída" />
            <div className="grade-indicadores indicadores-importacao">
              {[['Registros processados', resultado.processados], ['Adicionados', resultado.adicionados], ['Atualizados', resultado.atualizados], ['Registros com erro', resultado.erros]].map(([titulo, valor]) => <CartaoIndicador key={titulo} titulo={titulo} valor={valor.toLocaleString('pt-BR')} />)}
            </div>
            <div className="resumo-erros"><span>{resultado.erros} registros apresentaram problemas durante a importação simulada.</span><button className="botao-secundario" onClick={() => abrirDetalhes(resultado)}>Ver detalhes dos erros</button></div>
          </> : <p>Selecione uma planilha e clique em “Importar Dados” para iniciar.</p>}
        </div>
      </Cartao>
      <Cartao titulo="Histórico de Importações">
        <div className="rolagem-tabela" tabIndex={0} role="region" aria-label="Histórico de importações">
          <table><thead><tr>{['Arquivo', 'Data', 'Usuário', 'Registros', 'Status', 'Ações'].map((titulo) => <th key={titulo} scope="col">{titulo}</th>)}</tr></thead>
            <tbody>{historico.slice(inicio, inicio + porPagina).map((item) => <tr key={item.id}>
              <th scope="row">{item.arquivo}</th><td><time dateTime={item.data}>{item.data.split('-').reverse().join('/')}</time></td><td>{item.usuario}</td><td>{item.processados.toLocaleString('pt-BR')}</td>
              <td><span className={`etiqueta ${item.erros ? 'etiqueta-alerta' : 'etiqueta-sucesso'}`}>{obterSituacao(item)}</span></td>
              <td><button className="botao-detalhes" aria-label={`Ver detalhes de ${item.arquivo}`} onClick={() => abrirDetalhes(item)}>Ver detalhes</button></td>
            </tr>)}</tbody>
          </table>
        </div>
        <nav className="paginacao-importacao" aria-label="Páginas do histórico">
          <span>Mostrando {inicio + 1} a {Math.min(inicio + porPagina, historico.length)} de {historico.length} importações</span>
          <div><button className="botao-secundario" disabled={pagina === 1} onClick={() => definirPagina(pagina - 1)}>Anterior</button>
            {Array.from({ length: totalPaginas }, (_, indice) => <button key={indice} className="botao-secundario" aria-current={pagina === indice + 1 ? 'page' : undefined} aria-label={`Página ${indice + 1}`} onClick={() => definirPagina(indice + 1)}>{indice + 1}</button>)}
            <button className="botao-secundario" disabled={pagina === totalPaginas} onClick={() => definirPagina(pagina + 1)}>Próxima</button></div>
        </nav>
      </Cartao>
      <dialog ref={dialogo} className="dialogo-oportunidade" aria-labelledby="titulo-detalhes-importacao">
        <h2 id="titulo-detalhes-importacao">Detalhes da importação</h2>
        {detalhes && <><dl><dt>Arquivo</dt><dd>{detalhes.arquivo}</dd><dt>Status</dt><dd>{obterSituacao(detalhes)}</dd><dt>Registros processados</dt><dd>{detalhes.processados.toLocaleString('pt-BR')}</dd><dt>Registros com erro</dt><dd>{detalhes.erros.toLocaleString('pt-BR')}</dd></dl>
          <p>{detalhes.erros ? 'Este exemplo simula registros com problemas. As linhas e os motivos dos erros serão fornecidos pelo backend na integração.' : 'Este exemplo não apresenta registros com erro.'}</p></>}
        <form method="dialog"><button className="botao-principal">Fechar</button></form>
      </dialog>
    </main>
  )
}
