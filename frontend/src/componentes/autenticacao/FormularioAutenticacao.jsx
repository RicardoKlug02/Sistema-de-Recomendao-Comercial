import { useState } from 'react'
import CampoFormulario from '../CampoFormulario'
import useAcao from '../../hooks/useAcao'
import { entrar, registrar, validarFormulario } from '../../servicos/autenticacao'

export default function FormularioAutenticacao({ modo, aoEntrar, aoNavegar }) {
  const login = modo === 'entrar'
  const [nome, definirNome] = useState('')
  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [mensagem, definirMensagem] = useState('')
  const envio = useAcao()
  const enviando = envio.executando
  async function enviar(evento) {
    evento.preventDefault()
    const validacao = validarFormulario({ cadastro: !login, nome, email, senha })
    envio.definirErro(validacao)
    if (validacao) return
    await envio.executar(async () => {
      if (login) aoEntrar(await entrar({ email, senha }))
      else {
        const resposta = await registrar({ nome, email, senha })
        definirMensagem(resposta.mensagem)
        definirSenha('')
      }
    })
  }
  return <form className="formulario-autenticacao" onSubmit={enviar} noValidate>
    {!login && <CampoFormulario id="nome" rotulo="Nome" value={nome} onChange={(e) => definirNome(e.target.value)} disabled={enviando} />}
    <CampoFormulario id="email" rotulo="E-mail" type="email" autoComplete="username" value={email} onChange={(e) => definirEmail(e.target.value)} disabled={enviando} />
    <CampoFormulario id="senha" rotulo="Senha" type="password" autoComplete={login ? 'current-password' : 'new-password'} value={senha} onChange={(e) => definirSenha(e.target.value)} disabled={enviando} />
    {envio.erro && <p role="alert" className="erro-campo">{envio.erro}</p>}
    {mensagem && <p role="status">{mensagem}</p>}
    <button className="botao-principal" disabled={enviando}>{enviando ? 'Aguarde…' : login ? 'Entrar' : 'Solicitar acesso'}</button>
    <button type="button" className="botao-texto" disabled={enviando} onClick={aoNavegar}>{login ? 'Solicitar cadastro' : 'Voltar ao login'}</button>
    <small>O primeiro acesso após uma pausa do servidor pode demorar. Para redefinir sua senha, contate o administrador.</small>
  </form>
}
