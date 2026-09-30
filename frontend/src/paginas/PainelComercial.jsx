import { useEffect, useState } from 'react'
import Importacao from './Importacao'
import Clientes from './Clientes'
import Alertas from './Alertas'
import Usuarios from './Usuarios'
import VisaoGeral from './VisaoGeral'
import MenuLateral from '../componentes/MenuLateral'
import useDados from '../servicos/useDados'
import './PainelComercial.css'
import './Operacao.css'

const secoes = {
  painel: 'Visão geral',
  clientes: 'Clientes',
  alertas: 'Alertas',
  importacoes: 'Importação',
  usuarios: 'Usuários',
}

// O shell coordena navegação e invalidação das consultas após uma importação confirmada.
export default function PainelComercial({ usuario, aoSair, referenciaTitulo }) {
  const [secao, definirSecao] = useState('painel')
  const [clienteId, definirCliente] = useState(null)
  const [versao, definirVersao] = useState(0)
  const cadastroVendedores = useDados('/comercial/vendedores', versao)
  const atualizar = () => definirVersao((v) => v + 1)
  const gestor = ['admin', 'gestor'].includes(usuario.perfil)
  function abrirCliente(id) {
    definirCliente(id)
    definirSecao('clientes')
  }
  function navegar(destino) {
    if (destino === 'clientes') definirCliente(null)
    definirSecao(destino)
  }
  useEffect(() => {
    document.title = `${secoes[secao]} | Rio Verde Representações`
    document.querySelector('.conteudo-painel h1')?.focus()
  }, [secao])
  return (
    <div className="estrutura-painel">
      <a
        className="atalho-conteudo"
        href="#conteudo"
        onClick={(e) => {
          e.preventDefault()
          document.querySelector('.conteudo-painel h1')?.focus()
        }}
      >
        Pular para o conteúdo
      </a>
      <MenuLateral
        usuario={usuario}
        aoSair={aoSair}
        secaoAtiva={secao}
        aoNavegar={navegar}
      />
      <div className="barra-superior">
        <span>
          Rio Verde <span>/</span> {secoes[secao]}
        </span>
        <span>
          {new Date().toLocaleDateString('pt-BR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
        </span>
      </div>
      {secao === 'painel' && (
        <VisaoGeral
          vendedores={cadastroVendedores.dados || []}
          erroVendedores={cadastroVendedores.erro}
          versao={versao}
          aoAtualizar={atualizar}
          aoAbrirCliente={abrirCliente}
          aoAbrirAlertas={() => navegar('alertas')}
          referenciaTitulo={referenciaTitulo}
        />
      )}
      {secao === 'importacoes' && gestor && (
        <Importacao usuario={usuario} aoImportar={atualizar} />
      )}
      {secao === 'clientes' && (
        <Clientes key={clienteId || 'lista'} inicial={clienteId} />
      )}
      {secao === 'alertas' && (
        <Alertas
          vendedores={cadastroVendedores.dados || []}
          aoAbrirCliente={abrirCliente}
        />
      )}
      {secao === 'usuarios' && gestor && <Usuarios />}
    </div>
  )
}
