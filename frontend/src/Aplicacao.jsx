import { useEffect, useRef, useState } from 'react'
import CartaoAutenticacao from './componentes/autenticacao/CartaoAutenticacao'
import FormularioAutenticacao from './componentes/autenticacao/FormularioAutenticacao'
import PainelComercial from './paginas/PainelComercial'
import { tituloDocumento } from './secoes'
import { obterSessao, salvarSessao, solicitar } from './servicos/api'

const telas = {
  entrar: {
    titulo: 'Acesse sua carteira.',
    subtitulo: 'Informação para transformar sua próxima conversa.',
    alternativa: 'registrar',
  },
  registrar: {
    titulo: 'Solicitar acesso',
    subtitulo: 'Seu cadastro será aprovado pelo administrador',
    alternativa: 'entrar',
  },
}

export default function Aplicacao() {
  const [tela, definirTela] = useState('entrar')
  const [usuario, definirUsuario] = useState(null)
  const [verificando, definirVerificando] = useState(!!obterSessao())
  const [falhaSessao, definirFalhaSessao] = useState('')
  const [tentativa, definirTentativa] = useState(0)
  const referenciaTitulo = useRef(null)

  useEffect(() => {
    let ativa = true
    if (obterSessao())
      solicitar('/auth/me')
        .then((dados) => { if (ativa) definirUsuario(dados) })
        .catch((erro) => { if (ativa && obterSessao()) definirFalhaSessao(erro.message) })
        .finally(() => { if (ativa) definirVerificando(false) })
    const expirar = () => { definirUsuario(null); definirTela('entrar'); definirFalhaSessao('') }
    window.addEventListener('sessao-expirada', expirar)
    return () => {
      ativa = false
      window.removeEventListener('sessao-expirada', expirar)
    }
  }, [tentativa])

  useEffect(() => {
    if (usuario || verificando) return
    referenciaTitulo.current?.focus()
    document.title = tituloDocumento('Acesso')
  }, [tela, usuario, verificando])

  function sair() {
    salvarSessao(null)
    definirUsuario(null)
    definirTela('entrar')
    definirFalhaSessao('')
  }

  if (verificando) return <main className="pagina-autenticacao"><p role="status">Verificando acesso…</p></main>
  if (falhaSessao) return <main className="pagina-autenticacao">
    <CartaoAutenticacao titulo="Não foi possível verificar o acesso" subtitulo="Sua sessão foi mantida. Tente de novo quando a conexão voltar." referenciaTitulo={referenciaTitulo}>
      <p role="alert">{falhaSessao}</p>
      <button className="botao-principal" onClick={() => { definirFalhaSessao(''); definirVerificando(true); definirTentativa(n => n + 1) }}>Tentar novamente</button>
      <button className="botao-secundario" onClick={sair}>Sair da conta</button>
    </CartaoAutenticacao>
  </main>
  if (usuario) return <PainelComercial usuario={usuario} aoSair={sair} />
  const { titulo, subtitulo, alternativa } = telas[tela]
  return (
    <main className="pagina-autenticacao">
      <CartaoAutenticacao titulo={titulo} subtitulo={subtitulo} referenciaTitulo={referenciaTitulo}>
        <FormularioAutenticacao key={tela} modo={tela} aoEntrar={definirUsuario} aoNavegar={() => definirTela(alternativa)} />
      </CartaoAutenticacao>
    </main>
  )
}
