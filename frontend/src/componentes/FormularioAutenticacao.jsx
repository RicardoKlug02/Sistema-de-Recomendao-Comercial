import { useRef, useState } from 'react'
import CampoFormulario from './CampoFormulario'
import { entrar, validarEmail } from '../servicos/autenticacao'

// Envia credenciais reais e apresenta a resposta da API sem simular sucesso.
export default function FormularioAutenticacao({ aoEntrar }) {
  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [erros, definirErros] = useState({})
  const [erroSolicitacao, definirErroSolicitacao] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const solicitacaoPendente = useRef(false)
  async function enviarFormulario(evento) {
    evento.preventDefault()
    if (solicitacaoPendente.current) return
    const novosErros = { email: validarEmail(email), senha: senha ? '' : 'Informe sua senha.' }
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
      const resultado = await entrar({ email, senha })
      definirSenha('')
      aoEntrar(resultado.usuario)
    } catch (erro) {
      definirErroSolicitacao(erro.message)
    } finally {
      solicitacaoPendente.current = false
      definirEnviando(false)
    }
  }
  return (
    <form className="formulario-autenticacao" onSubmit={enviarFormulario} noValidate aria-busy={enviando}>
      <CampoFormulario
        id="email"
        rotulo="E-mail"
        type="email"
        autoComplete="username"
        placeholder="seu@email.com"
        value={email}
        erro={erros.email}
        disabled={enviando}
        onChange={(evento) => definirEmail(evento.target.value)}
      />
      <CampoFormulario
        id="senha"
        rotulo="Senha"
        type="password"
        autoComplete="current-password"
        placeholder="Sua senha"
        value={senha}
        erro={erros.senha}
        disabled={enviando}
        onChange={(evento) => definirSenha(evento.target.value)}
      />
      {erroSolicitacao && (
        <p className="erro-campo" role="alert">
          {erroSolicitacao}
        </p>
      )}
      <button className="botao-principal" disabled={enviando}>
        {enviando ? 'Entrando…' : 'Entrar'}
      </button>
      <p className="nota-informativa">
        Se precisar de acesso ou recuperar a senha, fale com o administrador.
      </p>
    </form>
  )
}
