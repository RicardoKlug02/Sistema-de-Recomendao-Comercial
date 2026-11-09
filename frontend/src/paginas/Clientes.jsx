import { useEffect, useState } from 'react'
import { TAMANHO_PAGINA } from '../configuracao'
import { useEstadoPagina, useRolagemPagina } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import CartaoCliente from '../componentes/clientes/CartaoCliente'
import FichaCliente from '../componentes/clientes/FichaCliente'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Icone from '../componentes/Icone'
import Pagina from '../componentes/Pagina'
import Paginacao from '../componentes/Paginacao'
import Seletor from '../componentes/Seletor'
import { montarCaminho } from '../servicos/api'

const textosVoltar = { alertas: 'Voltar aos alertas', painel: 'Voltar à visão geral' }

// Lista e ficha compartilham a página, sem consultas desnecessárias da lista no detalhe.
export default function Clientes({ inicial = null, fabricas = [], fabricaInicial, origem, aoVoltar }) {
  const [fabrica, definirFabrica] = useEstadoPagina('clientes.fabrica', fabricaInicial ?? '', inicial !== null && fabricaInicial !== undefined)
  const [busca, definirBusca] = useEstadoPagina('clientes.busca', '')
  const [termo, definirTermo] = useEstadoPagina('clientes.termo', '')
  const [pagina, definirPagina] = useEstadoPagina('clientes.pagina', 1)
  const [clienteId, definirCliente] = useState(inicial)
  const [rede, definirRede] = useState(true)
  const lista = useDados(clienteId ? null : montarCaminho('/comercial/clientes', {
    termo, pagina, limite: TAMANHO_PAGINA.clientes, fabrica_id: fabrica,
  }))
  useRolagemPagina('clientes', !!lista.dados, !clienteId)
  useEffect(() => { if (clienteId) window.scrollTo(0, 0) }, [clienteId])
  return (
    <Pagina
      titulo={clienteId ? 'Cliente 360º' : 'Sua carteira de clientes'}
      descricao={clienteId ? 'Histórico, ciclos e oportunidades em uma só visão.' : 'Conheça cada relacionamento. Prepare sua próxima visita.'}
    >
      {!clienteId && (
        <>
          <form className="filtros-comerciais faixa-filtros" onSubmit={(e) => { e.preventDefault(); definirTermo(busca); definirPagina(1) }}>
            <label className="campo-busca">
              Nome, documento, rede ou cidade
              <input placeholder="Encontre um cliente na sua carteira…" value={busca} onChange={(e) => definirBusca(e.target.value)} />
            </label>
            <button className="botao-secundario"><Icone nome="busca" tamanho={17} /> Buscar</button>
            <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={(v) => { definirFabrica(v); definirPagina(1) }} />
            {lista.dados && <span className="total-resultados">{lista.dados.total} clientes</span>}
          </form>
          <EstadoConsulta carregando={lista.carregando} erro={lista.erro} aoTentar={lista.tentarNovamente} vazio={lista.dados?.total === 0}
            mensagem="Nenhum cliente encontrado. Tente outro nome, rede ou cidade." />
          <div className="grade-cartoes">
            {lista.dados?.itens.map((c) => <CartaoCliente key={c.id} cliente={c} aoAbrir={definirCliente} />)}
          </div>
          {lista.dados && (
            <Paginacao pagina={pagina} total={lista.dados.total} tamanho={TAMANHO_PAGINA.clientes} aoMudar={definirPagina} unidade="clientes" />
          )}
        </>
      )}
      {clienteId && (
        <div className="ficha-cliente">
          <button className="botao-texto voltar-clientes" onClick={() => {
            if (aoVoltar) return aoVoltar()
            definirCliente(null)
            definirRede(true)
          }}>
            ← {textosVoltar[origem] || 'Voltar para clientes'}
          </button>
          <label className="opcao-rede">
            <input type="checkbox" checked={rede} onChange={(e) => definirRede(e.target.checked)} />{' '}
            Cliente comercial: agrupar todos os CNPJs da rede
          </label>
          <div className="filtros-comerciais"><Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={definirFabrica} /></div>
          <FichaCliente clienteId={clienteId} rede={rede} fabrica={fabrica}
            aoConsultarCadastro={(id) => { definirCliente(id); definirRede(false) }} />
        </div>
      )}
    </Pagina>
  )
}
