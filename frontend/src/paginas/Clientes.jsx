import { useState } from 'react'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import CartaoCliente from '../componentes/CartaoCliente'
import EstadoConsulta from '../componentes/EstadoConsulta'
import FichaCliente from '../componentes/FichaCliente'
import Icone from '../componentes/Icone'
import Paginacao from '../componentes/Paginacao'
import Seletor from '../componentes/Seletor'
import useDados from '../hooks/useDados'

const TAMANHO_PAGINA = 30

export default function Clientes({ clienteId, aoSelecionar, fabricas }) {
  const [busca, definirBusca] = useState('')
  const [termo, definirTermo] = useState('')
  const [pagina, definirPagina] = useState(1)
  const [fabrica, definirFabrica] = useState('')
  const [rede, definirRede] = useState(true)
  const parametros = new URLSearchParams({ termo, pagina, limite: TAMANHO_PAGINA })
  if (fabrica) parametros.set('fabrica_id', fabrica)
  const lista = useDados(clienteId ? null : `/comercial/clientes?${parametros}`)
  const filtroFabrica = (aoMudar) => (
    <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={aoMudar} />
  )
  function abrir(id, agruparRede) {
    definirRede(agruparRede)
    aoSelecionar(id)
  }
  return (
    <main className="conteudo-painel">
      <CabecalhoPagina
        titulo={clienteId ? 'Cliente 360º' : 'Sua carteira de clientes'}
        descricao={
          clienteId
            ? 'Histórico, ciclos e oportunidades em uma só visão.'
            : 'Conheça cada relacionamento. Prepare sua próxima visita.'
        }
      />
      {clienteId ? (
        <div className="ficha-cliente">
          <button className="botao-texto voltar-clientes" onClick={() => abrir(null, true)}>
            ← Voltar para clientes
          </button>
          <label className="opcao-rede">
            <input type="checkbox" checked={rede} onChange={(e) => definirRede(e.target.checked)} /> Cliente comercial:
            agrupar todos os CNPJs da rede
          </label>
          <div className="filtros-comerciais">{filtroFabrica(definirFabrica)}</div>
          <FichaCliente
            clienteId={clienteId}
            rede={rede}
            fabrica={fabrica}
            aoConsultarCadastro={(id) => abrir(id, false)}
          />
        </div>
      ) : (
        <>
          <form
            className="filtros-comerciais faixa-filtros"
            onSubmit={(e) => {
              e.preventDefault()
              definirTermo(busca)
              definirPagina(1)
            }}
          >
            <label className="campo-busca">
              Nome, documento, rede ou cidade
              <input
                placeholder="Encontre um cliente na sua carteira…"
                value={busca}
                onChange={(e) => definirBusca(e.target.value)}
              />
            </label>
            <button className="botao-secundario">
              <Icone nome="busca" tamanho={17} /> Buscar
            </button>
            {filtroFabrica((v) => {
              definirFabrica(v)
              definirPagina(1)
            })}
            {lista.dados && <span className="total-resultados">{lista.dados.total} clientes</span>}
          </form>
          <EstadoConsulta
            carregando={lista.carregando}
            erro={lista.erro}
            vazio={lista.dados?.total === 0}
            mensagem="Nenhum cliente encontrado. Tente outro nome, rede ou cidade."
          />
          <div className="grade-cartoes">
            {lista.dados?.itens.map((c) => (
              <CartaoCliente key={c.id} cliente={c} aoAbrir={(id) => abrir(id, true)} />
            ))}
          </div>
          {lista.dados && (
            <Paginacao
              pagina={pagina}
              total={lista.dados.total}
              tamanho={TAMANHO_PAGINA}
              aoMudar={definirPagina}
              unidade="clientes"
            />
          )}
        </>
      )}
    </main>
  )
}
