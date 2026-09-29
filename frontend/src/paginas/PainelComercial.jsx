import { useEffect, useState } from 'react'
import Importacao from './Importacao'
import VisaoGeral from './VisaoGeral'
import Clientes from './Clientes'
import MenuLateral from '../componentes/MenuLateral'
import DetalhesCliente from '../componentes/comercial/DetalhesCliente'
import './PainelComercial.css'

const titulos = { painel: 'Visão geral', clientes: 'Clientes', importacoes: 'Importação' }

// Após importar, as consultas abertas são invalidadas e recarregadas da API.
export default function PainelComercial({ usuario, aoSair }) {
  const [secaoAtiva, definirSecaoAtiva] = useState('painel')
  const [clienteSelecionado, definirClienteSelecionado] = useState(null)
  const [versao, definirVersao] = useState(0)
  const identificadorTitulo = secaoAtiva === 'importacoes' ? 'titulo-importacao' : `titulo-${secaoAtiva}`
  useEffect(() => {
    document.title = `${titulos[secaoAtiva]} | Rio Verde Representações`
    document.getElementById(identificadorTitulo)?.focus({ preventScroll: true })
    window.scrollTo({ top: 0 })
  }, [secaoAtiva, identificadorTitulo])
  function atualizar() {
    definirVersao((anterior) => anterior + 1)
  }
  const propriedades = { versao, aoAtualizar: atualizar, aoAbrirCliente: definirClienteSelecionado }
  return (
    <div className="estrutura-painel">
      <a className="atalho-conteudo" href={`#${identificadorTitulo}`}>
        Pular para o conteúdo
      </a>
      <MenuLateral usuario={usuario} aoSair={aoSair} secaoAtiva={secaoAtiva} aoNavegar={definirSecaoAtiva} />
      <div className="barra-superior">
        <span>
          Seu espaço comercial <span aria-hidden="true">/</span> <strong>{titulos[secaoAtiva]}</strong>
        </span>
        <span className="estado-sistema">Carteira comercial</span>
      </div>
      {secaoAtiva === 'painel' && (
        <VisaoGeral {...propriedades} aoVerClientes={() => definirSecaoAtiva('clientes')} />
      )}
      {secaoAtiva === 'clientes' && <Clientes {...propriedades} />}
      <Importacao usuario={usuario} ativa={secaoAtiva === 'importacoes'} aoImportar={atualizar} />
      {clienteSelecionado && (
        <DetalhesCliente
          key={clienteSelecionado.id}
          cliente={clienteSelecionado}
          versao={versao}
          aoFechar={() => definirClienteSelecionado(null)}
        />
      )}
    </div>
  )
}
