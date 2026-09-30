import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import Icone from '../componentes/comercial/Icone'
import GraficoMensal from '../componentes/graficos/GraficoMensal'
import RankingBarras from '../componentes/graficos/RankingBarras'
import useDados from '../servicos/useDados'
import { formatarMoeda } from '../servicos/dadosPainel'

// Mantém os filtros e contratos da main; apresentação e gráficos são independentes da API.
export default function VisaoGeral({
  vendedores,
  erroVendedores,
  versao,
  aoAtualizar,
  aoAbrirCliente,
  aoAbrirAlertas,
  referenciaTitulo,
}) {
  const [mes, definirMes] = useState('')
  const [vendedor, definirVendedor] = useState('')
  const parametros = new URLSearchParams()
  if (mes) parametros.set('mes', mes)
  if (vendedor) parametros.set('vendedor_id', vendedor)
  const consulta = useDados(`/comercial/painel?${parametros}`, versao)
  const dados = consulta.dados
  const indicadores = dados?.indicadores
  const mesAtivo = mes || dados?.mes || ''
  return (
    <main className="conteudo-painel" id="conteudo">
      <CabecalhoPagina
        titulo="Visão geral"
        descricao="Um olhar sobre sua carteira. Clareza para a próxima visita."
        referencia={referenciaTitulo}
      >
        <span className="etiqueta etiqueta-neutra">
          <span className="ponto-status" /> Dados do histórico importado
        </span>
      </CabecalhoPagina>
      <div className="filtros-comerciais faixa-filtros">
        <label>
          <span>
            <Icone nome="calendario" tamanho={15} /> Período
          </span>
          <input
            type="month"
            value={mesAtivo}
            onChange={(e) => definirMes(e.target.value)}
          />
        </label>
        <label>
          Vendedor
          <select
            aria-label="Vendedor"
            value={vendedor}
            onChange={(e) => definirVendedor(e.target.value)}
          >
            <option value="">Toda a equipe</option>
            {vendedores.map((v) => (
              <option key={v.id} value={v.id}>
                {v.nome}
              </option>
            ))}
          </select>
        </label>
        <button
          className="botao-secundario"
          onClick={aoAtualizar}
          disabled={consulta.carregando}
        >
          <Icone nome="atualizar" tamanho={16} /> Atualizar
        </button>
      </div>
      <EstadoConsulta
        erro={consulta.erro || erroVendedores}
        carregando={consulta.carregando}
        aoTentar={aoAtualizar}
      />
      {indicadores && (
        <>
          <div className="grade-indicadores">
            {[
              ['Faturamento', formatarMoeda(indicadores.venda_total), 'vendas'],
              ['Pedidos emitidos', indicadores.pedidos_emitidos, 'painel'],
              [
                'Clientes atendidos',
                indicadores.clientes_atendidos,
                'clientes',
              ],
              [
                'Ticket médio',
                formatarMoeda(indicadores.ticket_medio),
                'grafico',
              ],
            ].map(([titulo, valor, icone], i) => (
              <CartaoIndicador
                key={titulo}
                titulo={titulo}
                valor={valor}
                icone={icone}
                detalhe="No período selecionado"
                destaque={i === 0}
              />
            ))}
          </div>
          <div className="grade-indicadores grade-secundaria">
            {[
              [
                'Novos clientes',
                indicadores.clientes_novos,
                'Primeira compra no escritório',
              ],
              [
                'Aberturas por fábrica',
                indicadores.aberturas_cliente_fabrica,
                'Novas relações cliente–fábrica',
              ],
              [
                'Clientes reativados',
                indicadores.clientes_reativados,
                'Retorno após 90 dias sem compra',
              ],
            ].map(([titulo, valor, detalhe]) => (
              <CartaoIndicador
                key={titulo}
                titulo={titulo}
                valor={valor}
                detalhe={detalhe}
                icone="clientes"
              />
            ))}
          </div>
          <EstadoConsulta
            vazio={indicadores.pedidos_emitidos === 0}
            mensagem="Nenhum pedido neste período. Escolha outro mês ou importe as planilhas."
          />
          <div className="grade-resumos">
            <Cartao
              titulo="Evolução do faturamento"
              descricao="12 meses até o período selecionado"
              className="cartao-evolucao"
              acao={<Icone nome="grafico" />}
            >
              <GraficoMensal
                dados={dados.faturamento_mensal}
                mesSelecionado={mesAtivo}
              />
            </Cartao>
            <Cartao
              titulo="Fábricas em destaque"
              descricao="Participação em valor vendido"
            >
              <RankingBarras itens={dados.fabricas} />
            </Cartao>
            <Cartao
              titulo="Principais clientes"
              descricao="Relacionamentos que movimentam sua carteira"
            >
              <RankingBarras
                itens={dados.clientes}
                aoSelecionar={aoAbrirCliente}
              />
            </Cartao>
            <Cartao
              titulo="Vendas por região"
              descricao="Regiões imediatas a partir da localização do cliente"
            >
              <RankingBarras
                itens={(dados.regioes || []).map((r) => ({
                  ...r,
                  chave: `${r.uf}:${r.nome}`,
                  nome: `${r.nome} · ${r.uf}`,
                }))}
              />
            </Cartao>
            <Cartao
              titulo="Produtos em destaque"
              descricao="Ranking por valor dos itens vendidos"
            >
              <RankingBarras
                itens={(dados.produtos || []).map((p) => ({
                  ...p,
                  detalhe: `${p.quantidade} unidades vendidas`,
                }))}
              />
            </Cartao>
            <Cartao
              titulo="Novas relações comerciais"
              descricao="Primeira compra de cada cliente na fábrica"
            >
              <ul
                className="lista-aberturas"
                tabIndex={0}
                aria-label="Novas relações comerciais"
              >
                {(dados.aberturas || []).map((a) => (
                  <li key={`${a.cliente_id}:${a.fabrica}`}>
                    <span className="avatar avatar-pequeno">
                      <Icone nome="clientes" tamanho={16} />
                    </span>
                    <div>
                      <button
                        className="botao-detalhes"
                        onClick={() => aoAbrirCliente(a.cliente_id)}
                      >
                        {a.cliente}
                      </button>
                      <p>
                        {a.fabrica} · {a.data}
                      </p>
                      {a.novo_no_escritorio && (
                        <span className="etiqueta">Novo no escritório</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
              {!dados.aberturas?.length && (
                <p className="texto-vazio">Nenhuma abertura no período.</p>
              )}
            </Cartao>
            <Cartao
              titulo="Fábricas em crescimento"
              descricao="Comparação com o mês anterior"
            >
              <ul
                className="lista-clientes"
                tabIndex={0}
                aria-label="Fábricas em crescimento"
              >
                {(dados.fabricas_quentes || []).map((f) => (
                  <li key={f.nome}>
                    <span>{f.nome}</span>
                    <strong className="etiqueta etiqueta-sucesso">
                      +{f.crescimento}%
                    </strong>
                  </li>
                ))}
              </ul>
              {!dados.fabricas_quentes?.length && (
                <p className="texto-vazio">
                  Sem crescimento comparável no período.
                </p>
              )}
            </Cartao>
            <Cartao
              titulo="Sua próxima conversa começa aqui"
              descricao="Acompanhe os sinais do histórico e prepare cada contato."
              className="cartao-chamada"
            >
              <Icone nome="oportunidade" tamanho={32} />
              <p>
                Encontre clientes para o segundo pedido, fábricas próximas da
                inatividade e oportunidades de reposição.
              </p>
              <button className="botao-secundario" onClick={aoAbrirAlertas}>
                Explorar alertas <Icone nome="seta" tamanho={16} />
              </button>
            </Cartao>
          </div>
          <p className="nota-painel">
            Indicadores calculados sobre o histórico importado. Novos clientes
            também contam como aberturas por fábrica.{' '}
            {indicadores.pedidos_sem_itens} pedidos sem itens: seus valores
            entram no faturamento, mas não no ranking de produtos.
          </p>
        </>
      )}
    </main>
  )
}
