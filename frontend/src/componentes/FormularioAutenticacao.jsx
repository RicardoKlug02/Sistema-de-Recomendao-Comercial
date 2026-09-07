import { useRef, useState } from 'react'
import CampoFormulario from './CampoFormulario'
import { entrar, solicitarRecuperacaoSenha, validarEmail } from '../servicos/autenticacao'

export default function FormularioAutenticacao({ modo, aoEntrar, aoNavegar }) {
  const ehLogin = modo === 'entrar'
  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [erros, definirErros] = useState({})
  const [erroSolicitacao, definirErroSolicitacao] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const [concluido, definirConcluido] = useState(false)
  const solicitacaoPendente = useRef(false)

  async function enviarFormulario(evento) {
    evento.preventDefault()
    if (solicitacaoPendente.current || concluido) return
    const novosErros = {
      email: validarEmail(email),
      senha: ehLogin && !senha.trim() ? 'Informe sua senha.' : '',
    }
    definirErros(novosErros)
    definirErroSolicitacao('')
    const primeiroInvalido = Object.keys(novosErros).find((chave) => novosErros[chave])
    if (primeiroInvalido) {
      evento.currentTarget.elements.namedItem(primeiroInvalido).focus()
      return
    }
    solicitacaoPendente.current = true
    definirEnviando(true)
    try {
      if (ehLogin) {
        const resultado = await entrar({ email, senha })
        definirSenha('')
        aoEntrar(resultado.usuario)
      } else {
        await solicitarRecuperacaoSenha({ email })
        definirConcluido(true)
      }
    } catch {
      definirErroSolicitacao(ehLogin
        ? 'Não foi possível entrar. Tente novamente.'
        : 'Não foi possível solicitar a recuperação. Tente novamente.')
    } finally {
      solicitacaoPendente.current = false
      definirEnviando(false)
    }
  }

  return (
    <form className="formulario-autenticacao" onSubmit={enviarFormulario} noValidate aria-busy={enviando}>
      {concluido ? (
        <p className="mensagem-retorno" role="status">
          Solicitação simulada para <strong>{email.trim()}</strong>.
        </p>
      ) : (
        <>
          <CampoFormulario id="email" rotulo="Email" type="email" autoComplete={ehLogin ? 'username' : 'email'}
            placeholder="usuario@rioverdeindaial.com.br" value={email} erro={erros.email}
            disabled={enviando} onChange={(evento) => {
              definirEmail(evento.target.value)
              definirErros((anteriores) => ({ ...anteriores, email: '' }))
            }} />
          {ehLogin && <CampoFormulario id="senha" rotulo="Senha" type="password" autoComplete="current-password"
            placeholder="Digite sua senha aqui" value={senha} erro={erros.senha}
            disabled={enviando} onChange={(evento) => {
              definirSenha(evento.target.value)
              definirErros((anteriores) => ({ ...anteriores, senha: '' }))
            }} />}
          {erroSolicitacao && <p className="erro-campo" role="alert">{erroSolicitacao}</p>}
          <button className="botao-principal" type="submit" disabled={enviando}>
            {enviando ? (ehLogin ? 'Entrando…' : 'Solicitando…') : (ehLogin ? 'Entrar' : 'Recuperar senha')}
          </button>
          <span className="somente-leitor" role="status">{enviando ? 'Aguarde, processando solicitação.' : ''}</span>
        </>
      )}
      <button className="botao-texto" type="button" disabled={enviando} onClick={aoNavegar}>
        {ehLogin ? 'Esqueceu a senha?' : 'Voltar para o login'}
      </button>
    </form>
  )
}
