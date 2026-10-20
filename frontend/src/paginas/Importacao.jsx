import { useId, useState } from 'react'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import Cartao from '../componentes/Cartao'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Tabela from '../componentes/Tabela'
import useDados from '../hooks/useDados'
import { formatarMoeda } from '../servicos/formatacao'
import { importarArquivos } from '../servicos/importacao'


export default function Importacao({ aoImportar }) {
  const confirmacaoId = useId()
  const [cabecalho, definirCabecalho] = useState(null)
  const [itens, definirItens] = useState(null)
  const [erro, definirErro] = useState('')
  const [resultado, definirResultado] = useState(null)
  const [conferencia, definirConferencia] = useState(null)
  const [confirmado, definirConfirmado] = useState(false)
  const [enviando, definirEnviando] = useState(false)
  const [versao, definirVersao] = useState(0)
  const historico = useDados('/cargas/historico', versao)

  function descartarConferencia() {
    definirConferencia(null)
    definirConfirmado(false)
  }

  function selecionarArquivo(definir) {
    return (e) => {
      definir(e.target.files[0])
      descartarConferencia()
      definirResultado(null)
    }
  }

  async function importar(e) {
    e.preventDefault()
    definirEnviando(true)
    definirErro('')
    definirResultado(null)
    try {
      if (conferencia) {
        definirResultado(await importarArquivos(cabecalho, itens, conferencia.token_conferencia))
        descartarConferencia()
        definirVersao((v) => v + 1)
        aoImportar()
      } else definirConferencia(await importarArquivos(cabecalho, itens))
    } catch (falha) {
      definirErro(falha.message)
      descartarConferencia()
    } finally {
      definirEnviando(false)
    }
  }

  return (
    <main className="conteudo-painel tela-importacao">
      <CabecalhoPagina
        titulo="Importação de dados"
        descricao="Confira suas planilhas e mantenha o histórico comercial atualizado."
      />
      <Cartao titulo="Importar planilhas">
        <form onSubmit={importar} className="formulario-carga">
          <label>
            1. Cabeçalhos dos pedidos
            <input
              type="file"
              accept=".xls,.xlsx"
              required
              disabled={enviando}
              onChange={selecionarArquivo(definirCabecalho)}
            />
          </label>
          <label>
            2. Itens vendidos
            <input
              type="file"
              accept=".xls,.xlsx"
              required
              disabled={enviando}
              onChange={selecionarArquivo(definirItens)}
            />
          </label>
          <p>Pedidos fechados diretamente pela fábrica podem não ter itens. Eles entram normalmente no faturamento.</p>
          {conferencia && (
            <section aria-label="Conferência da importação">
              <h2>Confira antes de importar</h2>
              <p>
                Período: {conferencia.inicio} a {conferencia.fim}. Valor total dos arquivos:{' '}
                {formatarMoeda(conferencia.valor_total)}.
              </p>
              <p>
                {conferencia.processados} pedidos: {conferencia.adicionados} novos, {conferencia.atualizados}{' '}
                atualizações e {conferencia.itens} linhas de itens. {conferencia.pedidos_sem_itens} pedidos sem itens
                nesta carga.
              </p>
              {conferencia.avisos.map((aviso) => (
                <p key={aviso}>{aviso}</p>
              ))}
              <Tabela colunas={['Pedido', 'Cliente', 'Fábrica', 'Data', 'Valor', 'Ação']}>
                {conferencia.pedidos.map((p) => (
                  <tr key={`${p.fabrica}:${p.pedido}`}>
                    <td>{p.pedido}</td>
                    <td>{p.cliente}</td>
                    <td>{p.fabrica}</td>
                    <td>{p.data}</td>
                    <td>{formatarMoeda(p.valor)}</td>
                    <td>{p.acao}</td>
                  </tr>
                ))}
              </Tabela>
              {conferencia.processados > 100 && (
                <p>A tabela mostra os primeiros 100 pedidos. Os totais incluem todos os pedidos.</p>
              )}
              <div className="confirmacao-carga">
                <input
                  id={confirmacaoId}
                  type="checkbox"
                  checked={confirmado}
                  disabled={enviando}
                  onChange={(e) => definirConfirmado(e.target.checked)}
                />
                <label htmlFor={confirmacaoId}>Confirmo que as planilhas contêm somente vendas efetivadas que geram comissão.</label>
              </div>
            </section>
          )}
          <button
            className="botao-principal"
            disabled={enviando || !cabecalho || !itens || (conferencia && !confirmado)}
          >
            {enviando ? 'Processando planilhas…' : conferencia ? 'Confirmar importação' : 'Conferir planilhas'}
          </button>
        </form>
        {erro && (
          <p className="erro-campo" role="alert">
            {erro}
          </p>
        )}
        {resultado && (
          <div role="status">
            <p>
              {resultado.processados} pedidos: {resultado.adicionados} novos e {resultado.atualizados} atualizados;{' '}
              {resultado.itens} itens importados.
            </p>
            {resultado.avisos.map((aviso) => (
              <p key={aviso}>{aviso}</p>
            ))}
          </div>
        )}
      </Cartao>
      <Cartao titulo="Histórico de importações">
        <EstadoConsulta
          carregando={historico.carregando}
          erro={historico.erro}
          aoTentar={historico.tentarNovamente}
          vazio={historico.dados?.length === 0}
          mensagem="Nenhuma importação realizada."
        />
        {historico.dados?.length > 0 && (
          <Tabela colunas={['Pedidos', 'Itens', 'Data', 'Usuário', 'Pedidos processados']}>
            {historico.dados.map((h) => (
              <tr key={h.id}>
                <td>{h.arquivo}</td>
                <td>{h.arquivo_itens}</td>
                <td>{h.data}</td>
                <td>{h.usuario}</td>
                <td>{h.processados}</td>
              </tr>
            ))}
          </Tabela>
        )}
      </Cartao>
    </main>
  )
}
