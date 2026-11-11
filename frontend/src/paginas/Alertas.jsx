import { useState } from 'react'
import { TAMANHO_PAGINA } from '../configuracao'
import { useEstadoPagina, useRolagemPagina } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import AcompanhamentoAlerta from '../componentes/alertas/AcompanhamentoAlerta'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Icone from '../componentes/Icone'
import OrigemInformacao from '../componentes/OrigemInformacao'
import Pagina from '../componentes/Pagina'
import Paginacao from '../componentes/Paginacao'
import Seletor from '../componentes/Seletor'
import { montarCaminho } from '../servicos/api'
import { situacoesAcompanhamento, tiposAlerta } from '../servicos/alertas'
import { dataLocal, formatarData, formatarMoeda } from '../servicos/formatacao'

export default function Alertas({ vendedores, aoAbrirCliente, fabricas = [], rotina = false }) {
  const [fabrica, definirFabrica] = useEstadoPagina('alertas.fabrica', '')
  const [tipo, definirTipo] = useEstadoPagina('alertas.tipo', '')
  const [vendedor, definirVendedor] = useEstadoPagina('alertas.vendedor', '')
  const [pagina, definirPagina] = useEstadoPagina('alertas.pagina', 1)
  const [situacao, definirSituacao] = useEstadoPagina('alertas.situacao', '')
  const [sucesso, definirSucesso] = useState('')
  const resposta = useDados(montarCaminho('/comercial/alertas', {
    pagina, limite: TAMANHO_PAGINA.alertas, tipo, vendedor_id: vendedor, fabrica_id: fabrica, situacao, rotina: rotina || undefined,
  }))
  useRolagemPagina('alertas', !!resposta.dados)
  const filtrar = (definir) => (valor) => { definir(valor); definirPagina(1) }
  const clientes = resposta.dados?.total ?? 0
  const totalSinais = resposta.dados?.total_alertas ?? clientes
  return (
    <Pagina titulo={rotina ? 'Hoje' : 'Central de alertas'} className={rotina ? 'tela-hoje' : ''} descricao="Veja quem precisa de atenção e o que abordar no próximo contato.">
      <details className="filtros-alertas" open={!rotina}>
        <summary>Filtros da carteira</summary>
        <div className="filtros-comerciais faixa-filtros">
        <Seletor rotulo="Acompanhamento" todos="Todos os acompanhamentos" opcoes={situacoesAcompanhamento} valor={situacao} aoMudar={filtrar(definirSituacao)} />
        <Seletor rotulo="Tipo de oportunidade" todos="Todos os alertas" opcoes={tiposAlerta} valor={tipo} aoMudar={filtrar(definirTipo)} />
        <Seletor rotulo="Vendedor" todos="Toda a equipe" opcoes={vendedores} valor={vendedor} aoMudar={filtrar(definirVendedor)} />
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={filtrar(definirFabrica)} />
        </div>
      </details>
      {resposta.dados && <p className="total-resultados">{clientes} {clientes === 1 ? 'cliente' : 'clientes'} · {totalSinais} {totalSinais === 1 ? 'sinal' : 'sinais'}</p>}
      <EstadoConsulta carregando={resposta.carregando} erro={resposta.erro} aoTentar={resposta.tentarNovamente}
        vazio={resposta.dados?.total === 0} mensagem="Nenhum alerta para os filtros selecionados." />
      {sucesso && <p role="status">{sucesso}</p>}
      <div className="grade-cartoes">
        {resposta.dados?.itens.map((a) => {
          const sinais = a.alertas || [a]
          const dataRetorno = a.acompanhamento?.proximo_contato
          const hoje = dataLocal()
          const restantes = sinais.slice(3)
          return (
            <article className="cartao cartao-alerta" key={a.id}>
              <div className="topo-cliente">
                <span className="icone-indicador"><Icone nome="alertas" /></span>
                <span className={`etiqueta ${a.prioridade === 1 ? 'etiqueta-alerta' : ''}`}>
                  {dataRetorno && dataRetorno <= hoje ? (dataRetorno < hoje ? 'Retorno vencido' : 'Retorno hoje') : a.prioridade === 1 ? 'Prioridade alta' : 'Oportunidade'}
                </span>
              </div>
              <h2>{a.cliente}</h2>
              {a.volume_compras_12m != null && <small>Compras em 12 meses{fabrica ? ' nesta fábrica' : ''}: <strong>{formatarMoeda(a.volume_compras_12m)}</strong></small>}
              {dataRetorno && <p>Retorno combinado para <strong>{formatarData(dataRetorno)}</strong>.</p>}
              <ul className="sinais-em-destaque" aria-label="Sinais em destaque">
                {sinais.slice(0, 3).map(sinal => <Sinal key={sinal.id} sinal={sinal} />)}
              </ul>
              {restantes.length > 0 && <details className="alertas-agrupados"><summary>Ver mais {restantes.length} {restantes.length === 1 ? 'sinal' : 'sinais'}</summary><ul>
                {restantes.map(sinal => <Sinal key={sinal.id} sinal={sinal} />)}
              </ul></details>}
              <button className="botao-abrir" onClick={() => aoAbrirCliente(a.cliente_id, { fabrica })}>
                Consultar cliente <Icone nome="seta" tamanho={17} />
              </button>
              <AcompanhamentoAlerta key={`${a.id}:${a.acompanhamento?.versao || 0}:${a.assinatura}`} grupo={a} aoSalvar={() => { definirSucesso(`Acompanhamento de ${a.cliente} salvo.`); resposta.tentarNovamente() }} />
            </article>
          )
        })}
      </div>
      {resposta.dados && (
        <Paginacao pagina={pagina} total={resposta.dados.total} tamanho={TAMANHO_PAGINA.alertas} aoMudar={definirPagina} unidade="clientes" />
      )}
      <details className="nota-painel"><summary>Como os sinais são calculados?</summary>
        <p>A ordem considera o valor das compras registradas nos últimos 12 meses. Em Hoje, os retornos vencidos e os marcados para o dia vêm antes. Dentro do cliente, os sinais gerais aparecem antes dos sinais por fábrica, ordenados pelo valor comprado em cada uma.</p>
        <p>O lembrete de segundo pedido começa 14 dias após a primeira compra registrada na base e dá lugar à reativação a partir de 90 dias. Fábricas próximas da inatividade ficam em destaque do 76º ao 89º dia. Os sinais dependem do histórico importado.</p>
      </details>
    </Pagina>
  )
}

function Sinal({ sinal }) {
  return <li><strong>{tiposAlerta[sinal.tipo] || sinal.tipo}</strong><p>{sinal.descricao}</p>
    {sinal.tipo?.startsWith('FABRICA_') && sinal.volume_fabrica_12m != null && <small>Compras nesta fábrica em 12 meses: {formatarMoeda(sinal.volume_fabrica_12m)}</small>}
    <OrigemInformacao origem={sinal.origem} titulo="Ver pedido de referência" />
  </li>
}
