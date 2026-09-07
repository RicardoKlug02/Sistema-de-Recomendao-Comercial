import { useRef, useState } from 'react'
import MenuLateral from '../componentes/MenuLateral'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import { dadosPainel, formatarMoeda } from '../servicos/dadosPainel'
import './PainelComercial.css'

// Compõe os resumos comerciais e controla navegação e detalhes das oportunidades.
export default function PainelComercial({ usuario, aoSair, referenciaTitulo }) {
  const [secaoAtiva, definirSecaoAtiva] = useState('painel')
  const [oportunidadeSelecionada, definirOportunidadeSelecionada] = useState(null)
  const referenciaDialogo = useRef(null)
  const maiorFaturamento = Math.max(...dadosPainel.faturamentoMensal.map(({ valor }) => valor))

  function navegarParaSecao(destino) {
    definirSecaoAtiva(destino)
    const secao = document.getElementById(destino)
    secao?.focus({ preventScroll: true })
    secao?.scrollIntoView({ block: 'start' })
  }

  function abrirDetalhes(oportunidade) {
    definirOportunidadeSelecionada(oportunidade)
    referenciaDialogo.current.showModal()
  }

  return (
    <div className="estrutura-painel">
      <a className="atalho-conteudo" href="#painel">Pular para o conteúdo</a>
      <MenuLateral usuario={usuario} aoSair={aoSair} secaoAtiva={secaoAtiva} aoNavegar={navegarParaSecao} />
      <main className="conteudo-painel">
        <header className="cabecalho-painel">
          <div><p className="sobretitulo">VISÃO COMERCIAL</p><h1 id="painel" ref={referenciaTitulo} tabIndex={-1}>Dashboard</h1><p>Visão geral do desempenho comercial</p></div>
          <span className="aviso-demonstracao">Dados demonstrativos</span>
        </header>
        <div className="grade-indicadores">
          {dadosPainel.indicadores.map((indicador) => <CartaoIndicador key={indicador.titulo} {...indicador} />)}
        </div>
        <div className="grade-resumos">
          <Cartao titulo="Faturamento mensal" descricao="Últimos 12 meses · ago/2025 a jul/2026">
            <div className="grafico-colunas" role="list" aria-label="Faturamento por mês">
              {dadosPainel.faturamentoMensal.map(({ mes, valor }) => (
                <div key={mes} className="coluna-mensal" role="listitem" tabIndex={0} aria-label={`${mes}: ${formatarMoeda(valor)}`}>
                  <span className="valor-coluna">{formatarMoeda(valor)}</span>
                  <div className="trilho-coluna" aria-hidden="true"><span style={{ height: `${valor / maiorFaturamento * 100}%` }} /></div>
                  <span aria-hidden="true">{mes}</span>
                </div>
              ))}
            </div>
          </Cartao>
          <Cartao titulo="Vendas por categoria" descricao="Participação no total de vendas">
            <ul className="lista-categorias">
              {dadosPainel.categorias.map(({ nome, percentual }) => (
                <li key={nome}><span>{nome}</span><meter min="0" max="100" value={percentual} aria-label={nome}>{percentual}%</meter><strong>{percentual}%</strong></li>
              ))}
            </ul>
          </Cartao>
          <Cartao id="clientes" titulo="Top 5 clientes por faturamento" descricao="Clientes com maior volume de negócios">
            <ol className="lista-clientes">
              {dadosPainel.clientes.map(({ nome, faturamento }) => <li key={nome}><span>{nome}</span><strong>{formatarMoeda(faturamento)}</strong></li>)}
            </ol>
          </Cartao>
          <Cartao id="importacoes" titulo="Últimas importações" descricao="Histórico recente de arquivos">
            <ul className="lista-importacoes">
              {dadosPainel.importacoes.map(({ arquivo, data, situacao, registros }) => (
                <li key={arquivo}>
                  <div className="arquivo-importado"><strong>{arquivo}</strong><time dateTime={data}>{data.split('-').reverse().join('/')}</time></div>
                  <div className="resumo-importacao"><span className={`etiqueta ${situacao === 'Com erros' ? 'etiqueta-alerta' : 'etiqueta-sucesso'}`}>{situacao}</span><span>{registros.toLocaleString('pt-BR')} registros</span></div>
                </li>
              ))}
            </ul>
          </Cartao>
        </div>
        <Cartao titulo="Oportunidades recentes" descricao="Recomendações para suas próximas vendas" className="cartao-oportunidades">
          <div className="rolagem-tabela" tabIndex={0} role="region" aria-label="Oportunidades recentes">
            <table>
              <thead><tr>{['Cliente', 'Produto / Linha', 'Relevância', 'Valor estimado', 'Ação'].map((titulo) => <th key={titulo} scope="col">{titulo}</th>)}</tr></thead>
              <tbody>{dadosPainel.oportunidades.map((oportunidade) => (
                <tr key={oportunidade.id}>
                  <th scope="row">{oportunidade.cliente}</th><td>{oportunidade.produto}</td>
                  <td><span className={`etiqueta relevancia-${oportunidade.relevancia.toLowerCase()}`}>{oportunidade.relevancia}</span></td>
                  <td className="valor-monetario">{formatarMoeda(oportunidade.valor)}</td>
                  <td><button className="botao-detalhes" onClick={() => abrirDetalhes(oportunidade)} aria-label={`Ver detalhes da oportunidade de ${oportunidade.cliente}`}>Ver detalhes <span aria-hidden="true">↗</span></button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </Cartao>
        <p className="nota-painel">Ambiente de demonstração · Valores ilustrativos, sem conexão com dados reais.</p>
      </main>
      <dialog ref={referenciaDialogo} className="dialogo-oportunidade" aria-labelledby="titulo-oportunidade">
        <h2 id="titulo-oportunidade">Detalhes da oportunidade</h2>
        {oportunidadeSelecionada && <dl>
          <dt>Cliente</dt><dd>{oportunidadeSelecionada.cliente}</dd>
          <dt>Produto / Linha</dt><dd>{oportunidadeSelecionada.produto}</dd>
          <dt>Relevância</dt><dd>{oportunidadeSelecionada.relevancia}</dd>
          <dt>Valor estimado</dt><dd>{formatarMoeda(oportunidadeSelecionada.valor)}</dd>
        </dl>}
        <p>Recomendação demonstrativa para análise comercial.</p>
        <form method="dialog"><button className="botao-principal">Fechar</button></form>
      </dialog>
    </div>
  )
}
