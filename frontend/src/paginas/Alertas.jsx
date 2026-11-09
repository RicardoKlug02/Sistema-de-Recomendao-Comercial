import { useState } from 'react'
import { TAMANHO_PAGINA } from '../configuracao'
import { useEstadoPagina, useRolagemPagina } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import AcompanhamentoAlerta from '../componentes/alertas/AcompanhamentoAlerta'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Icone from '../componentes/Icone'
import Pagina from '../componentes/Pagina'
import Paginacao from '../componentes/Paginacao'
import Seletor from '../componentes/Seletor'
import { montarCaminho } from '../servicos/api'
import { proximaAcao, situacoesAcompanhamento, tiposAlerta } from '../servicos/alertas'

export default function Alertas({ vendedores, aoAbrirCliente, fabricas = [] }) {
  const [fabrica, definirFabrica] = useEstadoPagina('alertas.fabrica', '')
  const [tipo, definirTipo] = useEstadoPagina('alertas.tipo', '')
  const [vendedor, definirVendedor] = useEstadoPagina('alertas.vendedor', '')
  const [pagina, definirPagina] = useEstadoPagina('alertas.pagina', 1)
  const [situacao, definirSituacao] = useEstadoPagina('alertas.situacao', '')
  const [sucesso, definirSucesso] = useState('')
  const resposta = useDados(montarCaminho('/comercial/alertas', {
    pagina, limite: TAMANHO_PAGINA.alertas, tipo, vendedor_id: vendedor, fabrica_id: fabrica, situacao,
  }))
  useRolagemPagina('alertas', !!resposta.dados)
  const filtrar = (definir) => (valor) => { definir(valor); definirPagina(1) }
  return (
    <Pagina titulo="Central de alertas" descricao="Os sinais da sua carteira, transformados em próximos passos.">
      <div className="filtros-comerciais faixa-filtros">
        <Seletor rotulo="Acompanhamento" todos="Todos os acompanhamentos" opcoes={situacoesAcompanhamento} valor={situacao} aoMudar={filtrar(definirSituacao)} />
        <Seletor rotulo="Tipo de oportunidade" todos="Todos os alertas" opcoes={tiposAlerta} valor={tipo} aoMudar={filtrar(definirTipo)} />
        <Seletor rotulo="Vendedor" todos="Toda a equipe" opcoes={vendedores} valor={vendedor} aoMudar={filtrar(definirVendedor)} />
        {resposta.dados && (
          <span className="total-resultados">
            {resposta.dados.total} clientes · {resposta.dados.total_alertas ?? resposta.dados.total} alertas
          </span>
        )}
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={filtrar(definirFabrica)} />
      </div>
      <EstadoConsulta carregando={resposta.carregando} erro={resposta.erro} aoTentar={resposta.tentarNovamente}
        vazio={resposta.dados?.total === 0} mensagem="Nenhum alerta para os filtros selecionados." />
      {sucesso && <p role="status">{sucesso}</p>}
      <div className="grade-cartoes">
        {resposta.dados?.itens.map((a) => {
          const sinais = a.alertas || [a]
          return (
            <article className="cartao cartao-alerta" key={a.id}>
              <div className="topo-cliente">
                <span className="icone-indicador"><Icone nome="alertas" /></span>
                <span className={`etiqueta ${a.prioridade === 1 ? 'etiqueta-alerta' : ''}`}>
                  {a.prioridade === 1 ? 'Prioridade alta' : 'Acompanhamento'}
                </span>
              </div>
              <h2>{a.cliente}</h2>
              <p className="descricao-alerta">{sinais.length} {sinais.length === 1 ? 'sinal' : 'sinais'} para acompanhar neste cliente.</p>
              <p className="resumo-alerta">{Object.entries(a.resumo || { [a.tipo]: 1 }).map(([id, total]) => `${total} × ${tiposAlerta[id] || id}`).join(' · ')}</p>
              <p><strong>Próxima ação:</strong> {proximaAcao(a.resumo)}</p>
              <details className="alertas-agrupados"><summary>Ver fábricas e produtos</summary><ul>
                {sinais.map((sinal) => <li key={sinal.id}><strong>{tiposAlerta[sinal.tipo] || sinal.tipo}</strong><p>{sinal.descricao}</p></li>)}
              </ul></details>
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
      <p className="nota-painel">
        Segundo pedido: contato após 14 dias da primeira compra registrada na base. Importar históricos anteriores pode alterar esse
        enquadramento. Fábricas em risco a partir de 76 dias e inativas a partir de 90. Alertas calculados sob consulta, sem envio automático.
      </p>
    </Pagina>
  )
}
