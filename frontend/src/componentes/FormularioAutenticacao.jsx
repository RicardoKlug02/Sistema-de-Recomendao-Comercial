import { useRef, useState } from 'react'
import CampoFormulario from './CampoFormulario'
import { entrar, registrar, validarEmail } from '../servicos/autenticacao'

export default function FormularioAutenticacao({ modo, aoEntrar, aoNavegar }) {
  const login = modo === 'entrar'
  const [nome, definirNome] = useState('')
  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [erro, definirErro] = useState('')
  const [mensagem, definirMensagem] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const pendente = useRef(false)
  async function enviar(evento) {
    evento.preventDefault()
    if (pendente.current) return
    const validacao = validarEmail(email) || (!senha ? 'Informe a senha.' : '') ||
      (!login && (nome.trim().length < 2 || senha.length < 6) ? 'Informe nome e senha com pelo menos 6 caracteres.' : '')
    definirErro(validacao)
    if (validacao) return
    pendente.current = true
    definirEnviando(true)
    try {
      if (login) aoEntrar((await entrar({ email, senha })).usuario)
      else {
        const resposta = await registrar({ nome, email, senha })
        definirMensagem(resposta.mensagem)
        definirSenha('')
      }
    } catch (falha) { definirErro(falha.message) }
    finally { pendente.current = false; definirEnviando(false) }
  }
  return <form className="formulario-autenticacao" onSubmit={enviar}>
    {!login && <CampoFormulario id="nome" rotulo="Nome" value={nome} onChange={(e) => definirNome(e.target.value)} disabled={enviando} />}
    <CampoFormulario id="email" rotulo="E-mail" type="email" autoComplete="username" value={email} onChange={(e) => definirEmail(e.target.value)} disabled={enviando} />
    <CampoFormulario id="senha" rotulo="Senha" type="password" autoComplete={login ? 'current-password' : 'new-password'} value={senha} onChange={(e) => definirSenha(e.target.value)} disabled={enviando} />
    {erro && <p role="alert" className="erro-campo">{erro}</p>}
    {mensagem && <p role="status">{mensagem}</p>}
    <button className="botao-principal" disabled={enviando}>{enviando ? 'Aguarde…' : login ? 'Entrar' : 'Solicitar acesso'}</button>
    <button type="button" className="botao-texto" disabled={enviando} onClick={aoNavegar}>{login ? 'Solicitar cadastro' : 'Voltar ao login'}</button>
    <small>O primeiro acesso após uma pausa do servidor pode demorar. Para redefinir sua senha, contate o administrador.</small>
  </form>
}
