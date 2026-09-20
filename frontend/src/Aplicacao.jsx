import { useEffect, useRef, useState } from 'react'
import CartaoAutenticacao from './componentes/CartaoAutenticacao'
import FormularioAutenticacao from './componentes/FormularioAutenticacao'
import PainelComercial from './paginas/PainelComercial'
import './Autenticacao.css'

export default function Aplicacao() {
  const [tela, definirTela] = useState('entrar')
  const [usuario, definirUsuario] = useState(null)
  const referenciaTitulo = useRef(null)
  useEffect(() => {
    referenciaTitulo.current?.focus()
    const titulo = usuario ? 'Dashboard' : tela === 'entrar' ? 'Login' : 'Recuperar senha'
    document.title = `${titulo} | Sistema de Recomendação Comercial`
  }, [tela, usuario])

  function sair() {
    definirUsuario(null)
    definirTela('entrar')
  }

  if (usuario) return <PainelComercial usuario={usuario} aoSair={sair} referenciaTitulo={referenciaTitulo} />

  return (
    <main className="pagina-autenticacao">
      <CartaoAutenticacao
        titulo={tela === 'entrar' ? 'Sistema de Recomendação Rio Verde Rep' : 'Recuperar senha'}
        subtitulo={tela === 'entrar' ? 'Acesse sua conta para continuar' : 'Informe o e-mail da sua conta'}
        referenciaTitulo={referenciaTitulo}>
        <FormularioAutenticacao key={tela} modo={tela} aoEntrar={definirUsuario}
          aoNavegar={() => definirTela(tela === 'entrar' ? 'recuperar' : 'entrar')} />
      </CartaoAutenticacao>
    </main>
  )
}
