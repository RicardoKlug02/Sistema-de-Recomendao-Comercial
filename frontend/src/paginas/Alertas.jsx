import { useState } from 'react'
import useDados from '../servicos/useDados'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import Paginacao from '../componentes/comercial/Paginacao'
import Icone from '../componentes/comercial/Icone'

const tipos = {
  SEGUNDO_PEDIDO: 'Segundo pedido',
  CLIENTE_INATIVO: 'Cliente inativo',
  FABRICA_EM_RISCO: 'Fábrica próxima da inatividade',
  FABRICA_INATIVA: 'Fábrica inativa',
  PRODUTO_EM_RISCO: 'Produto em risco',
}

export default function Alertas({ vendedores, aoAbrirCliente }) {
  const [tipo, definirTipo] = useState('')
  const [vendedor, definirVendedor] = useState('')
  const [pagina, definirPagina] = useState(1)
  const resposta = useDados(
    `/comercial/alertas?pagina=${pagina}&tipo=${tipo}${vendedor ? `&vendedor_id=${vendedor}` : ''}`,
  )
  return (
    <main className="conteudo-painel" id="conteudo">
      <CabecalhoPagina
        titulo="Central de alertas"
        descricao="Os sinais da sua carteira, transformados em próximos passos."
      />
      <div className="filtros-comerciais faixa-filtros">
        <label>
          Tipo de oportunidade
          <select
            value={tipo}
            onChange={(e) => {
              definirTipo(e.target.value)
              definirPagina(1)
            }}
          >
            <option value="">Todos os alertas</option>
            {Object.entries(tipos).map(([chave, nome]) => (
              <option key={chave} value={chave}>
                {nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          Vendedor
          <select
            aria-label="Vendedor"
            value={vendedor}
            onChange={(e) => {
              definirVendedor(e.target.value)
              definirPagina(1)
            }}
          >
            <option value="">Toda a equipe</option>
            {vendedores.map((v) => (
              <option key={v.id} value={v.id}>
                {v.nome}
              </option>
            ))}
          </select>
        </label>
        {resposta.dados && (
          <span className="total-resultados">
            {resposta.dados.total} oportunidades encontradas
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
        {resposta.dados?.itens.map((a) => (
          <article className="cartao cartao-alerta" key={a.id}>
            <div className="topo-cliente">
              <span className="icone-indicador">
                <Icone nome="alertas" />
              </span>
              <span
                className={`etiqueta ${a.prioridade === 1 ? 'etiqueta-alerta' : ''}`}
              >
                {a.prioridade === 1 ? 'Prioridade alta' : 'Acompanhamento'}
              </span>
            </div>
            <p className="sobretitulo tipo-alerta">{tipos[a.tipo] || a.tipo}</p>
            <h2>{a.cliente}</h2>
            <p className="descricao-alerta">{a.descricao}</p>
            <button
              className="botao-abrir"
              onClick={() => aoAbrirCliente(a.cliente_id)}
            >
              Consultar cliente <Icone nome="seta" tamanho={17} />
            </button>
          </article>
        ))}
      </div>
      {resposta.dados && (
        <Paginacao
          pagina={pagina}
          total={resposta.dados.total}
          tamanho={50}
          aoMudar={definirPagina}
          unidade="alertas"
        />
      )}
      <p className="nota-painel">
        Segundo pedido após 14 dias; fábricas em risco a partir de 76 dias e
        inativas a partir de 90. Alertas calculados sob consulta, sem envio
        automático.
      </p>
    </main>
  )
}
