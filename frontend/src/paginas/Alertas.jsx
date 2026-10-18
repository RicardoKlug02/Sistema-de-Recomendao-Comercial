import { useState } from 'react'
import useDados from '../hooks/useDados'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Icone from '../componentes/Icone'
import Paginacao from '../componentes/Paginacao'
import Seletor from '../componentes/Seletor'

const TAMANHO_PAGINA = 50

const tipos = {
  SEGUNDO_PEDIDO: 'Segundo pedido',
  CLIENTE_INATIVO: 'Cliente inativo',
  FABRICA_EM_RISCO: 'Fábrica próxima da inatividade',
  FABRICA_INATIVA: 'Fábrica inativa',
  PRODUTO_EM_RISCO: 'Produto em risco',
}

export default function Alertas({ vendedores, fabricas, aoAbrirCliente }) {
  const [tipo, definirTipo] = useState('')
  const [vendedor, definirVendedor] = useState('')
  const [fabrica, definirFabrica] = useState('')
  const [pagina, definirPagina] = useState(1)
  const parametros = new URLSearchParams({ pagina, limite: TAMANHO_PAGINA })
  if (tipo) parametros.set('tipo', tipo)
  if (vendedor) parametros.set('vendedor_id', vendedor)
  if (fabrica) parametros.set('fabrica_id', fabrica)
  const resposta = useDados(`/comercial/alertas?${parametros}`)
  const filtrar = (definir) => (valor) => {
    definir(valor)
    definirPagina(1)
  }
  return (
    <main className="conteudo-painel">
      <CabecalhoPagina
        titulo="Central de alertas"
        descricao="Os sinais da sua carteira, transformados em próximos passos."
      />
      <div className="filtros-comerciais faixa-filtros">
        <Seletor
          rotulo="Tipo de oportunidade"
          todos="Todos os alertas"
          opcoes={Object.entries(tipos).map(([id, nome]) => ({ id, nome }))}
          valor={tipo}
          aoMudar={filtrar(definirTipo)}
        />
        <Seletor
          rotulo="Vendedor"
          todos="Toda a equipe"
          opcoes={vendedores}
          valor={vendedor}
          aoMudar={filtrar(definirVendedor)}
        />
        <Seletor
          rotulo="Fábrica"
          todos="Todas as fábricas"
          opcoes={fabricas}
          valor={fabrica}
          aoMudar={filtrar(definirFabrica)}
        />
        {resposta.dados && (
          <span className="total-resultados">
            {resposta.dados.total} clientes · {resposta.dados.total_alertas ?? resposta.dados.total} alertas
          </span>
        )}
      </div>
      <EstadoConsulta
        carregando={resposta.carregando}
        erro={resposta.erro}
        vazio={resposta.dados?.total === 0}
        mensagem="Nenhum alerta para os filtros selecionados."
      />
      <div className="grade-cartoes">
        {resposta.dados?.itens.map((a) => {
          const sinais = a.alertas || [a]
          return (
            <article className="cartao cartao-alerta" key={a.id}>
              <div className="topo-cliente">
                <span className="icone-indicador">
                  <Icone nome="alertas" />
                </span>
                <span className={`etiqueta ${a.prioridade === 1 ? 'etiqueta-alerta' : ''}`}>
                  {a.prioridade === 1 ? 'Prioridade alta' : 'Acompanhamento'}
                </span>
              </div>
              <h2>{a.cliente}</h2>
              <p className="descricao-alerta">
                {sinais.length} {sinais.length === 1 ? 'sinal' : 'sinais'} para acompanhar neste cliente.
              </p>
              <details className="alertas-agrupados">
                <summary>Ver fábricas e produtos</summary>
                <ul>
                  {sinais.map((sinal) => (
                    <li key={sinal.id}>
                      <strong>{tipos[sinal.tipo] || sinal.tipo}</strong>
                      <p>{sinal.descricao}</p>
                    </li>
                  ))}
                </ul>
              </details>
              <button className="botao-abrir" onClick={() => aoAbrirCliente(a.cliente_id)}>
                Consultar cliente <Icone nome="seta" tamanho={17} />
              </button>
            </article>
          )
        })}
      </div>
      {resposta.dados && (
        <Paginacao
          pagina={pagina}
          total={resposta.dados.total}
          tamanho={TAMANHO_PAGINA}
          aoMudar={definirPagina}
          unidade="clientes"
        />
      )}
      <p className="nota-painel">
        Segundo pedido após 14 dias; fábricas em risco a partir de 76 dias e inativas a partir de 90. Alertas calculados
        sob consulta, sem envio automático.
      </p>
    </main>
  )
}
