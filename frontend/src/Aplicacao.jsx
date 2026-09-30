import { useEffect, useRef, useState } from 'react'
import CartaoAutenticacao from './componentes/CartaoAutenticacao'
import FormularioAutenticacao from './componentes/FormularioAutenticacao'
import PainelComercial from './paginas/PainelComercial'
import { obterSessao, salvarSessao, solicitar } from './servicos/api'
import './Autenticacao.css'

export default function Aplicacao() {
  const [tela, definirTela] = useState('entrar')
  const [usuario, definirUsuario] = useState(null)
  const [verificando, definirVerificando] = useState(!!obterSessao())
  const referenciaTitulo = useRef(null)
  useEffect(() => {
    let ativa = true
    if (obterSessao())
      solicitar('/auth/me')
        .then((dados) => {
          if (ativa) definirUsuario(dados)
        })
        .catch(() => salvarSessao(null))
        .finally(() => {
          if (ativa) definirVerificando(false)
        })
    const expirar = () => {
      definirUsuario(null)
      definirTela('entrar')
    }
    window.addEventListener('sessao-expirada', expirar)
    return () => {
      ativa = false
      window.removeEventListener('sessao-expirada', expirar)
    }
  }, [])
  useEffect(() => {
    referenciaTitulo.current?.focus()
    document.title = `${usuario ? 'Painel' : 'Acesso'} | Rio Verde Representações`
  }, [tela, usuario])
  function sair() {
    salvarSessao(null)
    definirUsuario(null)
    definirTela('entrar')
  }
  if (verificando)
    return (
      <main className="pagina-autenticacao">
        <p role="status">Verificando acesso…</p>
      </main>
    )
  if (usuario)
    return (
      <PainelComercial
        usuario={usuario}
        aoSair={sair}
        referenciaTitulo={referenciaTitulo}
      />
    )
  return (
    <main className="pagina-autenticacao">
      <CartaoAutenticacao
        titulo={tela === 'entrar' ? 'Acesse sua carteira.' : 'Solicitar acesso'}
        subtitulo={
          tela === 'entrar'
            ? 'Informação para transformar sua próxima conversa.'
            : 'Seu cadastro será aprovado pelo administrador'
        }
        referenciaTitulo={referenciaTitulo}
      >
        <FormularioAutenticacao
          key={tela}
          modo={tela}
          aoEntrar={definirUsuario}
          aoNavegar={() =>
            definirTela(tela === 'entrar' ? 'registrar' : 'entrar')
          }
        />
      </CartaoAutenticacao>
    </main>
  )
}
