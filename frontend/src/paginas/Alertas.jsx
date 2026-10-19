import { useState } from 'react'
import { useEstadoPagina, useRolagemPagina } from '../servicos/estadoPaginas'
import AcompanhamentoAlerta from '../componentes/AcompanhamentoAlerta'
import { situacoesAcompanhamento } from '../servicos/acompanhamento'
import useDados from '../hooks/useDados'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Paginacao from '../componentes/Paginacao'
import Icone from '../componentes/Icone'
import Seletor from '../componentes/Seletor'

const tipos = {
  SEGUNDO_PEDIDO: 'Segundo pedido na base',
  CLIENTE_INATIVO: 'Cliente inativo',
  FABRICA_EM_RISCO: 'Fábrica próxima da inatividade',
  FABRICA_INATIVA: 'Fábrica inativa',
  PRODUTO_EM_RISCO: 'Produto em risco',
}

export default function Alertas({ vendedores, aoAbrirCliente, fabricas = [] }) {
  const [fabrica, definirFabrica] = useEstadoPagina('alertas.fabrica', '')
  const [tipo, definirTipo] = useEstadoPagina('alertas.tipo', '')
  const [vendedor, definirVendedor] = useEstadoPagina('alertas.vendedor', '')
  const [pagina, definirPagina] = useEstadoPagina('alertas.pagina', 1)
  const [situacao, definirSituacao] = useEstadoPagina('alertas.situacao', '')
  const [sucesso, definirSucesso] = useState('')
  const resposta = useDados(
    `/comercial/alertas?pagina=${pagina}&tipo=${tipo}${vendedor ? `&vendedor_id=${vendedor}` : ''}${fabrica ? `&fabrica_id=${fabrica}` : ''}${situacao ? `&situacao=${situacao}` : ''}`,
  )
  useRolagemPagina('alertas', !!resposta.dados)
  return (
    <main className="conteudo-painel" id="conteudo">
      <CabecalhoPagina
        titulo="Central de alertas"
        descricao="Os sinais da sua carteira, transformados em próximos passos."
      />
      <div className="filtros-comerciais faixa-filtros">
        <label>Acompanhamento<select aria-label="Acompanhamento" value={situacao} onChange={(e) => { definirSituacao(e.target.value); definirPagina(1) }}><option value="">Todos os acompanhamentos</option>{Object.entries(situacoesAcompanhamento).map(([id, nome]) => <option value={id} key={id}>{nome}</option>)}</select></label>
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
            {resposta.dados.total} clientes · {resposta.dados.total_alertas ?? resposta.dados.total} alertas
          </span>
        )}
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={(v) => { definirFabrica(v); definirPagina(1) }} />
      </div>
      <EstadoConsulta
        carregando={resposta.carregando}
        erro={resposta.erro}
        aoTentar={resposta.tentarNovamente}
        vazio={resposta.dados?.total === 0}
        mensagem="Nenhum alerta para os filtros selecionados."
      />
      {sucesso && <p role="status">{sucesso}</p>}
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
            <h2>{a.cliente}</h2>
            <p className="descricao-alerta">{a.alertas?.length || 1} {(a.alertas?.length || 1) === 1 ? 'sinal' : 'sinais'} para acompanhar neste cliente.</p>
            <p className="resumo-alerta">{Object.entries(a.resumo || { [a.tipo]: 1 }).map(([id, total]) => `${total} × ${tipos[id] || id}`).join(' · ')}</p>
            <p><strong>Próxima ação:</strong> {a.resumo?.CLIENTE_INATIVO || a.resumo?.FABRICA_INATIVA ? 'Revisar oportunidades de retorno.' : a.resumo?.SEGUNDO_PEDIDO ? 'Verificar o contato após a primeira compra registrada na base.' : 'Conferir o histórico e preparar o próximo contato.'}</p>
            <details className="alertas-agrupados"><summary>Ver fábricas e produtos</summary><ul>
              {(a.alertas || [a]).map((sinal) => <li key={sinal.id}><strong>{tipos[sinal.tipo] || sinal.tipo}</strong><p>{sinal.descricao}</p></li>)}
            </ul></details>
            <button
              className="botao-abrir"
              onClick={() => aoAbrirCliente(a.cliente_id, { fabrica })}
            >
              Consultar cliente <Icone nome="seta" tamanho={17} />
            </button>
            <AcompanhamentoAlerta key={`${a.id}:${a.acompanhamento?.versao || 0}:${a.assinatura}`} grupo={a} aoSalvar={() => { definirSucesso(`Acompanhamento de ${a.cliente} salvo.`); resposta.tentarNovamente() }} />
          </article>
        ))}
      </div>
      {resposta.dados && (
        <Paginacao
          pagina={pagina}
          total={resposta.dados.total}
          tamanho={50}
          aoMudar={definirPagina}
          unidade="clientes"
        />
      )}
      <p className="nota-painel">
        Segundo pedido: contato após 14 dias da primeira compra registrada na base.
        Importar históricos anteriores pode alterar esse enquadramento. Fábricas em risco a partir de 76 dias e
        inativas a partir de 90. Alertas calculados sob consulta, sem envio
        automático.
      </p>
    </main>
  )
}
