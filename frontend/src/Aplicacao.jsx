import { useEffect, useRef, useState } from 'react'
import CartaoAutenticacao from './componentes/CartaoAutenticacao'
import FormularioAutenticacao from './componentes/FormularioAutenticacao'
import PainelComercial from './paginas/PainelComercial'
import { encerrarSessao, obterSessao } from './servicos/api'
import './Autenticacao.css'

export default function Aplicacao() {
  const [usuario, definirUsuario] = useState(() => obterSessao()?.usuario || null)
  const [mensagem, definirMensagem] = useState('')
  const referenciaTitulo = useRef(null)
  useEffect(() => {
    function expirar() {
      definirUsuario(null)
      definirMensagem('Sua sessão expirou. Entre novamente para continuar.')
    }
    window.addEventListener('sessao-expirada', expirar)
    return () => window.removeEventListener('sessao-expirada', expirar)
  }, [])
  useEffect(() => {
    if (!usuario) {
      document.title = 'Login | Rio Verde Representações'
      referenciaTitulo.current?.focus()
    }
  }, [usuario])
  function sair() {
    encerrarSessao()
    definirUsuario(null)
    definirMensagem('')
  }
  if (usuario) return <PainelComercial usuario={usuario} aoSair={sair} />
  return (
    <main className="pagina-autenticacao">
      <CartaoAutenticacao
        titulo="Acesse sua carteira."
        subtitulo="Entre com sua conta para acompanhar os dados comerciais."
        referenciaTitulo={referenciaTitulo}
      >
        {mensagem && (
          <p className="erro-campo" role="alert">
            {mensagem}
          </p>
        )}
        <FormularioAutenticacao aoEntrar={definirUsuario} />
      </CartaoAutenticacao>
    </main>
  )
}
