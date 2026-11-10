import { useEstadoPagina, useRolagemPagina } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Icone from '../componentes/Icone'
import Pagina from '../componentes/Pagina'
import Seletor from '../componentes/Seletor'
import GraficoMensal from '../componentes/graficos/GraficoMensal'
import RankingBarras from '../componentes/graficos/RankingBarras'
import HistoricoDisponivel from '../componentes/visao-geral/HistoricoDisponivel'
import { montarCaminho } from '../servicos/api'
import { formatarData, formatarMoeda } from '../servicos/formatacao'

export default function VisaoGeral({ vendedores, fabricas = [], versao, aoAtualizar, aoAbrirCliente, aoAbrirAlertas }) {
  const [mes, definirMes] = useEstadoPagina('painel.mes', '')
  const [vendedor, definirVendedor] = useEstadoPagina('painel.vendedor', '')
  const [fabrica, definirFabrica] = useEstadoPagina('painel.fabrica', '')
  const consulta = useDados(montarCaminho('/comercial/painel', { mes, vendedor_id: vendedor, fabrica_id: fabrica }), versao)
  const dados = consulta.dados
  useRolagemPagina('painel', !!dados)
  const indicadores = dados?.indicadores
  const mesAtivo = mes || dados?.mes || ''
  const abrirCliente = (id) => aoAbrirCliente(id, { fabrica })
  const etiqueta = <span className="etiqueta etiqueta-neutra"><span className="ponto-status" /> Dados do histórico importado</span>
  return (
    <Pagina titulo="Visão geral" descricao="Um olhar sobre sua carteira. Clareza para a próxima visita." acoes={etiqueta}>
      <HistoricoDisponivel versao={versao} />
      <div className="filtros-comerciais faixa-filtros">
        <label>
          <span><Icone nome="calendario" tamanho={15} /> Período</span>
          <input type="month" value={mesAtivo} onChange={(e) => definirMes(e.target.value)} />
        </label>
        <Seletor rotulo="Vendedor" todos="Toda a equipe" opcoes={vendedores} valor={vendedor} aoMudar={definirVendedor} />
        <button className="botao-secundario" onClick={aoAtualizar} disabled={consulta.carregando}>
          <Icone nome="atualizar" tamanho={16} /> Atualizar
        </button>
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={definirFabrica} />
      </div>
      <EstadoConsulta erro={consulta.erro} carregando={consulta.carregando} aoTentar={aoAtualizar} />
      {indicadores && (
        <>
          <div className="grade-indicadores">
            {[
              ['Faturamento', formatarMoeda(indicadores.venda_total), 'vendas'],
              ['Pedidos emitidos', indicadores.pedidos_emitidos, 'painel'],
              ['Clientes atendidos', indicadores.clientes_atendidos, 'clientes'],
              ['Ticket médio', formatarMoeda(indicadores.ticket_medio), 'grafico'],
            ].map(([titulo, valor, icone], i) => (
              <CartaoIndicador key={titulo} titulo={titulo} valor={valor} icone={icone} detalhe="No período selecionado" destaque={i === 0} />
            ))}
          </div>
          <div className="grade-indicadores grade-secundaria">
            {[
              ['Novos clientes na base', indicadores.clientes_novos, 'Primeira compra registrada na base'],
              ['Aberturas por fábrica', indicadores.aberturas_cliente_fabrica, 'Primeira compra registrada na base por fábrica'],
              ['Clientes reativados', indicadores.clientes_reativados, 'Retorno após 90 dias sem compra'],
            ].map(([titulo, valor, detalhe]) => (
              <CartaoIndicador key={titulo} titulo={titulo} valor={valor} detalhe={detalhe} icone="clientes" />
            ))}
          </div>
          <EstadoConsulta vazio={indicadores.pedidos_emitidos === 0} mensagem="Nenhum pedido neste período. Escolha outro mês ou importe as planilhas." />
          <div className="grade-resumos">
            <Cartao titulo="Evolução do faturamento" descricao="12 meses até o período selecionado" className="cartao-evolucao" acao={<Icone nome="grafico" />}>
              <GraficoMensal dados={dados.faturamento_mensal} mesSelecionado={mesAtivo} />
            </Cartao>
            <Cartao titulo="Fábricas em destaque" descricao="Participação em valor vendido">
              <RankingBarras itens={dados.fabricas} />
            </Cartao>
            <Cartao titulo="Principais clientes" descricao="Relacionamentos que movimentam sua carteira">
              <RankingBarras itens={dados.clientes} aoSelecionar={abrirCliente} />
            </Cartao>
            <Cartao titulo="Vendas por região" descricao="Regiões imediatas a partir da localização do cliente">
              <RankingBarras itens={(dados.regioes || []).map((r) => ({ ...r, chave: `${r.uf}:${r.nome}`, nome: `${r.nome} · ${r.uf}` }))} />
            </Cartao>
            <Cartao titulo="Produtos em destaque" descricao="Ranking por valor dos itens vendidos">
              <RankingBarras itens={(dados.produtos || []).map((p) => ({
                ...p, detalhe: `${p.fabrica || 'Fábrica não informada'} · Código ${p.sku || 'não informado'} · ${p.quantidade} unidades vendidas`,
              }))} />
            </Cartao>
            <Cartao titulo="Novas relações comerciais" descricao="Primeira compra registrada na base de cada cliente na fábrica">
              <ul className="lista-aberturas" tabIndex={0} aria-label="Novas relações comerciais">
                {(dados.aberturas || []).map((a) => (
                  <li key={`${a.cliente_id}:${a.fabrica}`}>
                    <span className="avatar avatar-pequeno"><Icone nome="clientes" tamanho={16} /></span>
                    <div>
                      <button className="botao-detalhes" onClick={() => abrirCliente(a.cliente_id)}>{a.cliente}</button>
                      <p>{a.fabrica} · {formatarData(a.data)}</p>
                      {a.novo_no_escritorio && <span className="etiqueta">Primeira compra registrada na base</span>}
                    </div>
                  </li>
                ))}
              </ul>
              {!dados.aberturas?.length && <p className="texto-vazio">Nenhuma abertura no período.</p>}
            </Cartao>
            <Cartao titulo="Fábricas em crescimento" descricao="Comparação com o mês anterior">
              <ul className="lista-clientes" tabIndex={0} aria-label="Fábricas em crescimento">
                {(dados.fabricas_quentes || []).map((f) => (
                  <li key={f.nome}><span>{f.nome}</span><strong className="etiqueta etiqueta-sucesso">+{f.crescimento}%</strong></li>
                ))}
              </ul>
              {!dados.fabricas_quentes?.length && <p className="texto-vazio">Sem crescimento comparável no período.</p>}
            </Cartao>
            <Cartao titulo="Sua próxima conversa começa aqui" descricao="Acompanhe os sinais do histórico e prepare cada contato." className="cartao-chamada">
              <Icone nome="oportunidade" tamanho={32} />
              <p>Encontre clientes para o segundo pedido, fábricas próximas da inatividade e oportunidades de reposição.</p>
              <button className="botao-secundario" onClick={aoAbrirAlertas}>Explorar alertas <Icone nome="seta" tamanho={16} /></button>
            </Cartao>
          </div>
          <p className="nota-painel">
            Fonte: cabeçalhos importados para os valores; itens importados para o ranking de produtos. Os filtros de mês, vendedor e fábrica são aplicados aos indicadores. Clientes usam o cadastro atual da rede.{' '}
            Bonificações e duplicidades revisadas são desconsideradas. Ajustes comissionados entram no valor, mas não contam como compra, cliente atendido ou abertura e não entram no ticket médio.{' '}
            {indicadores.ajustes_comissionados_registros > 0 && <>Neste mês: {indicadores.ajustes_comissionados_registros} ajuste(s), no valor de {formatarMoeda(indicadores.ajustes_comissionados_valor)}.{' '}</>}
            Novos clientes e aberturas por fábrica representam a primeira compra registrada na base. Importar históricos anteriores
            pode alterar as datas e as classificações. Novos clientes também contam como aberturas por fábrica.{' '}
            {indicadores.pedidos_sem_itens} pedidos sem itens registrados na base: seus valores entram no faturamento, mas não no ranking de produtos.
          </p>
        </>
      )}
    </Pagina>
  )
}
