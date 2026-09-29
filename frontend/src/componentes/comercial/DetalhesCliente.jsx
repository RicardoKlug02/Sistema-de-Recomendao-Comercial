import { useEffect, useRef, useState } from 'react'
import { formatarMoeda, formatarNumero } from '../../servicos/dadosComerciais'
import useConsulta from '../../ganchos/useConsulta'
import EstadoConsulta from './EstadoConsulta'
import Etiqueta from './Etiqueta'
import Icone from './Icone'
import SugestoesComplementares from './SugestoesComplementares'

function ListaRecomendacoes({ titulo, descricao, itens, apresentar }) {
  return (
    <section className="secao-perfil">
      <h3>{titulo}</h3>
      <p>{descricao}</p>
      {itens.length ? (
        itens.map((item) => (
          <article className="oportunidade-perfil" key={item.produto_id}>
            <h4>{item.nome}</h4>
            <p>SKU {item.sku}</p>
            {apresentar(item)}
          </article>
        ))
      ) : (
        <p className="sem-alertas">Nenhuma indicação disponível para este cliente.</p>
      )}
    </section>
  )
}

// A ficha é consultada ao abrir, com cancelamento ao fechar e retorno do foco à origem.
export default function DetalhesCliente({ cliente, aoFechar, versao }) {
  const referenciaDialogo = useRef(null)
  const [tentativa, definirTentativa] = useState(0)
  const consulta = useConsulta(`/clientes/${cliente.id}`, `${versao}-${tentativa}`)
  const ficha = consulta.dados
  const valida = ficha && ficha.cliente_id === cliente.id
  useEffect(() => {
    const dialogo = referenciaDialogo.current
    const anterior = document.activeElement
    dialogo.showModal()
    return () => {
      dialogo.close()
      anterior?.focus()
    }
  }, [])
  const fabricas = ficha?.resumo_fabricas || []
  const reposicoes = ficha?.sugestoes_reposicao || []
  const abandonados = ficha?.produtos_em_abandono || []
  const expansao = ficha?.sugestoes_expansao_mix || []
  const comparacao = ficha?.performance_yoy
  const produtosReferencia = [
    ...new Map([...reposicoes, ...abandonados].map((item) => [item.produto_id, item])).values(),
  ]
  return (
    <dialog
      ref={referenciaDialogo}
      className="dialogo-cliente"
      aria-labelledby="nome-cliente"
      onClose={() => {
        if (!referenciaDialogo.current.open) aoFechar()
      }}
    >
      <header className="cabecalho-perfil">
        <div>
          <p className="sobretitulo">CLIENTE 360°</p>
          <h2 id="nome-cliente">{ficha?.razao_social || cliente.nome}</h2>
          {cliente.cidade && (
            <p>
              {cliente.cidade}
              {cliente.estado ? ` · ${cliente.estado}` : ''}
            </p>
          )}
        </div>
        <button
          className="botao-icone"
          aria-label="Fechar perfil do cliente"
          onClick={() => referenciaDialogo.current.close()}
        >
          <Icone nome="fechar" />
        </button>
      </header>
      <div className="corpo-perfil">
        <EstadoConsulta
          {...consulta}
          erro={
            consulta.erro ||
            (ficha && !valida ? 'A ficha retornada não corresponde ao cliente selecionado.' : '')
          }
          aoTentar={() => definirTentativa(tentativa + 1)}
        />
        {valida && (
          <>
            <dl className="dados-perfil">
              <div>
                <dt>CNPJ / CPF</dt>
                <dd>{ficha.cnpj_cpf || 'Não informado'}</dd>
              </div>
              <div>
                <dt>Região</dt>
                <dd>{ficha.micro_regiao || 'Não informado'}</dd>
              </div>
              <div>
                <dt>Grupo econômico</dt>
                <dd>{ficha.grupo_economico || 'Não informado'}</dd>
              </div>
            </dl>
            {ficha.mensagem && <p className="nota-informativa">{ficha.mensagem}</p>}
            <section className="secao-perfil" aria-labelledby="titulo-comparacao">
              <h3 id="titulo-comparacao">Faturamento em perspectiva</h3>
              {comparacao ? (
                <>
                  <div className="historico-cliente comparacao-cliente">
                    <div>
                      <span>{comparacao.periodo_recente}</span>
                      <strong>{formatarMoeda(comparacao.faturamento_recente)}</strong>
                    </div>
                    <div>
                      <span>{comparacao.periodo_comparado}</span>
                      <strong>{formatarMoeda(comparacao.faturamento_ano_anterior)}</strong>
                    </div>
                  </div>
                  <p>
                    {comparacao.faturamento_ano_anterior > 0
                      ? `${formatarNumero(comparacao.crescimento_pct)}% em relação ao período comparado.`
                      : 'Sem faturamento registrado no período comparado para calcular a variação.'}
                  </p>
                </>
              ) : (
                <p>Comparação de faturamento não disponível para este cliente.</p>
              )}
            </section>
            <section className="secao-perfil" aria-labelledby="titulo-fabricas">
              <h3 id="titulo-fabricas">Relacionamento por fábrica</h3>
              <p>Ciclos e sinais de inatividade baseados nas compras registradas.</p>
              {fabricas.length ? (
                fabricas.map((fabrica) => (
                  <article className="oportunidade-perfil" key={fabrica.fabrica_id}>
                    <div className="linha-cartao">
                      <h4>{fabrica.fabrica}</h4>
                      <Etiqueta texto={fabrica.status} />
                    </div>
                    <dl className="dados-perfil">
                      <div>
                        <dt>Última compra</dt>
                        <dd>{fabrica.ultima_compra}</dd>
                      </div>
                      <div>
                        <dt>Sem comprar</dt>
                        <dd>{fabrica.dias_sem_comprar} dias</dd>
                      </div>
                      <div>
                        <dt>Ciclo médio</dt>
                        <dd>{fabrica.ciclo_medio_dias} dias</dd>
                      </div>
                      <div>
                        <dt>Previsão pelo ciclo</dt>
                        <dd>
                          {fabrica.dias_para_vencer < 0
                            ? `${Math.abs(fabrica.dias_para_vencer)} dias em atraso`
                            : `Em ${fabrica.dias_para_vencer} dias`}
                        </dd>
                      </div>
                    </dl>
                    {fabrica.risco_bloqueio_neste_mes && (
                      <p className="aviso-fabrica">
                        Atinge o limite de inatividade em {fabrica.data_limite_inatividade}.
                      </p>
                    )}
                  </article>
                ))
              ) : (
                <p>Nenhuma fábrica com histórico disponível.</p>
              )}
            </section>
            <ListaRecomendacoes
              titulo="Reposição de produtos"
              descricao="Confira as próximas necessidades de compra."
              itens={reposicoes}
              apresentar={(item) => (
                <>
                  <Etiqueta texto={item.status} />
                  <p>
                    {item.dias_desde_ultima} dias desde a última compra · ciclo de {item.ciclo_medio} dias.
                  </p>
                  <p>Volume habitual: {formatarNumero(item.volume_habitual)} unidades.</p>
                  <div className="acao-sugerida">
                    <span>PRÓXIMO PASSO</span>
                    <p>Confirmar estoque e avaliar uma proposta de reposição.</p>
                  </div>
                </>
              )}
            />
            <ListaRecomendacoes
              titulo="Produtos em abandono"
              descricao="Itens recorrentes que deixaram de aparecer nos pedidos."
              itens={abandonados}
              apresentar={(item) => (
                <>
                  <p>
                    {item.dias_parado} dias sem compra · ciclo habitual de {item.ciclo_habitual} dias.
                  </p>
                  <p>{item.total_vezes_comprado} compras registradas.</p>
                  <div className="acao-sugerida">
                    <span>PRÓXIMO PASSO</span>
                    <p>Entender a mudança na demanda e avaliar a retomada do produto.</p>
                  </div>
                </>
              )}
            />
            <ListaRecomendacoes
              titulo="Possibilidades de expansão do mix"
              descricao="Sugestões do motor de recomendação para validar com o cliente."
              itens={expansao}
              apresentar={() => (
                <div className="acao-sugerida">
                  <span>PRÓXIMO PASSO</span>
                  <p>Apresentar o produto e verificar se atende às necessidades do cliente.</p>
                </div>
              )}
            />
            {produtosReferencia.length > 0 && <SugestoesComplementares produtos={produtosReferencia} />}
          </>
        )}
      </div>
    </dialog>
  )
}
