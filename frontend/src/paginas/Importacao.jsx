import { useEffect, useRef, useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import { importarArquivos, validarArquivo } from '../servicos/importacao'
import './Importacao.css'

// A API não expõe histórico: o resultado mostrado pertence apenas ao envio atual.
export default function Importacao({ usuario, ativa, aoImportar }) {
  const [arquivos, definirArquivos] = useState({ pedidos: null, itens: null })
  const [erro, definirErro] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const [resultado, definirResultado] = useState(null)
  const envioEmCurso = useRef(false)
  const controle = useRef(null)
  const podeImportar = ['admin', 'gestor'].includes(usuario.perfil)
  useEffect(() => () => controle.current?.abort(), [])
  function selecionar(tipo, lista) {
    if (envioEmCurso.current || !lista.length) return
    const falha = lista.length !== 1 ? 'Selecione uma planilha para cada campo.' : validarArquivo(lista[0])
    definirErro(falha)
    // Uma seleção inválida não pode reutilizar um arquivo anterior sem aviso.
    definirArquivos((atuais) => ({ ...atuais, [tipo]: falha ? null : lista[0] }))
    definirResultado(null)
  }
  async function importar() {
    if (envioEmCurso.current) return
    envioEmCurso.current = true
    controle.current = new AbortController()
    definirEnviando(true)
    definirErro('')
    definirResultado(null)
    try {
      const retorno = await importarArquivos(arquivos.pedidos, arquivos.itens, controle.current.signal)
      definirResultado(retorno)
      aoImportar()
    } catch (falha) {
      if (falha.name !== 'AbortError') definirErro(falha.message)
    } finally {
      envioEmCurso.current = false
      definirEnviando(false)
    }
  }
  return (
    <main className="conteudo-painel tela-importacao" hidden={!ativa}>
      <header className="cabecalho-painel">
        <div>
          <p className="sobretitulo">DADOS COMERCIAIS</p>
          <h1 id="titulo-importacao" tabIndex={-1}>
            Importação de dados
          </h1>
          <p>Envie os relatórios de pedidos e produtos vendidos do mesmo período.</p>
        </div>
      </header>
      {podeImportar ? (
        <Cartao
          titulo="Importar planilhas Excel"
          descricao="XLS ou XLSX · até 10 MB por arquivo nesta interface."
        >
          <div className="grade-arquivos">
            {[
              {
                tipo: 'pedidos',
                titulo: '1. Pedidos',
                descricao: 'Planilha de pedidos e cabeçalho exportada do ERP.',
              },
              {
                tipo: 'itens',
                titulo: '2. Produtos vendidos',
                descricao: 'Planilha de itens faturados por produto.',
              },
            ].map(({ tipo, titulo, descricao }) => (
              <label
                className="area-arquivo"
                key={tipo}
                onDragOver={(evento) => evento.preventDefault()}
                onDrop={(evento) => {
                  evento.preventDefault()
                  selecionar(tipo, evento.dataTransfer.files)
                }}
              >
                <strong>{titulo}</strong>
                <span>{descricao}</span>
                <input
                  type="file"
                  accept=".xls,.xlsx"
                  disabled={enviando}
                  aria-label={titulo}
                  onChange={(evento) => selecionar(tipo, evento.target.files)}
                />
                <small>
                  {arquivos[tipo] ? arquivos[tipo].name : 'Selecione ou arraste a planilha para este campo.'}
                </small>
              </label>
            ))}
          </div>
          <p className="nota-informativa">
            Os arquivos serão enviados ao servidor e poderão atualizar os dados comerciais. Aguarde a
            confirmação antes de reenviar.
          </p>
          {erro && (
            <p className="erro-campo" role="alert">
              {erro}
            </p>
          )}
          <button
            className="botao-principal botao-importar"
            disabled={enviando || !arquivos.pedidos || !arquivos.itens}
            onClick={importar}
          >
            {enviando ? 'Importando…' : 'Importar dados'}
          </button>
          {enviando && (
            <p role="status">
              Processando os arquivos. O servidor pode levar alguns minutos; você pode continuar navegando.
            </p>
          )}
          {resultado && (
            <div role="status">
              <p>{resultado.mensagem || 'O servidor confirmou o recebimento da importação.'}</p>
              <div className="grade-indicadores indicadores-importacao">
                {[
                  { campo: 'pedidos', titulo: 'Pedidos processados' },
                  { campo: 'itens', titulo: 'Itens processados' },
                  { campo: 'adicionados', titulo: 'Pedidos novos' },
                  { campo: 'atualizados', titulo: 'Pedidos atualizados' },
                ]
                  .filter(({ campo }) => typeof resultado[campo] === 'number')
                  .map(({ campo, titulo }) => (
                    <CartaoIndicador key={campo} titulo={titulo} valor={resultado[campo]} />
                  ))}
              </div>
              {Array.isArray(resultado.avisos) &&
                resultado.avisos.map((aviso) => (
                  <p key={aviso} className="nota-informativa">
                    {aviso}
                  </p>
                ))}
            </div>
          )}
        </Cartao>
      ) : (
        <Cartao titulo="Importação restrita">
          <p>
            Seu perfil pode consultar os dados. Para importar arquivos, solicite acesso de administrador ou
            gestor.
          </p>
        </Cartao>
      )}
      <p className="nota-painel">
        Após a confirmação, os alertas e as próximas consultas de clientes serão atualizados. O histórico de
        importações ainda não está disponível.
      </p>
    </main>
  )
}
