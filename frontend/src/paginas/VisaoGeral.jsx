import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import FiltrosCarteira from '../componentes/comercial/FiltrosCarteira'
import FiltrosTipo from '../componentes/comercial/FiltrosTipo'
import CartaoOportunidade from '../componentes/comercial/CartaoOportunidade'
import EstadoVazio from '../componentes/comercial/EstadoVazio'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import { adaptarAlerta, normalizarTexto } from '../servicos/dadosComerciais'
import useConsulta from '../ganchos/useConsulta'

const tipos = ['Todas', 'Reativação', 'Reposição']

export default function VisaoGeral({ versao, aoAtualizar, aoAbrirCliente, aoVerClientes }) {
  const [busca, definirBusca] = useState('')
  const [tipo, definirTipo] = useState('Todas')
  const [prioridade, definirPrioridade] = useState('')
  const [limite, definirLimite] = useState(12)
  const consulta = useConsulta('/clientes/alertas/home?limite=50', versao)
  const formatoInvalido = consulta.dados !== null && !Array.isArray(consulta.dados)
  const oportunidades = Array.isArray(consulta.dados) ? consulta.dados.map(adaptarAlerta) : []
  const filtradas = oportunidades.filter(
    (item) =>
      (!prioridade || item.prioridade === prioridade) &&
      normalizarTexto(`${item.cliente.nome} ${item.produto} ${item.sku || ''}`).includes(
        normalizarTexto(busca.trim()),
      ),
  )
  const selecionadas = filtradas.filter((item) => tipo === 'Todas' || item.tipo === tipo)
  const disponivel = !consulta.carregando && !consulta.erro && !formatoInvalido
  const valor = (numero) => (disponivel ? numero : '—')
  return (
    <main className="conteudo-painel">
      <CabecalhoPagina
        titulo="Um olhar para o que vem a seguir."
        descricao="Priorize suas conversas com os alertas de recompra da carteira."
        identificador="titulo-painel"
      />
      <FiltrosCarteira
        busca={busca}
        aoBuscar={definirBusca}
        rotulo="Buscar nos alertas recebidos"
        campos={[
          {
            nome: 'prioridade',
            titulo: 'Prioridade',
            valor: prioridade,
            aoAlterar: definirPrioridade,
            opcoes: [
              { valor: '', rotulo: 'Todas as prioridades' },
              { valor: 'Alta', rotulo: 'Alta' },
              { valor: 'Média', rotulo: 'Média' },
            ],
          },
        ]}
      />
      <div className="linha-contexto">
        <span>Até 50 alertas prioritários retornados pelo servidor</span>
        <button className="botao-detalhes" onClick={aoAtualizar} disabled={consulta.carregando}>
          Atualizar alertas
        </button>
      </div>
      <div className="grade-indicadores">
        <CartaoIndicador
          titulo="Alertas recebidos"
          valor={valor(oportunidades.length)}
          detalhe="Recorte prioritário da carteira"
        />
        <CartaoIndicador
          titulo="Alta prioridade"
          valor={valor(oportunidades.filter((item) => item.prioridade === 'Alta').length)}
          detalhe="Risco crítico de interrupção de compra"
        />
        <CartaoIndicador
          titulo="Clientes nos alertas"
          valor={valor(new Set(oportunidades.map((item) => item.cliente.id)).size)}
          detalhe="Clientes associados aos alertas recebidos"
        />
        <CartaoIndicador
          titulo="Reposições atrasadas"
          valor={valor(oportunidades.filter((item) => item.tipo === 'Reposição').length)}
          detalhe="Oportunidades de retomar o ciclo"
        />
      </div>
      <EstadoConsulta
        {...consulta}
        erro={
          consulta.erro ||
          (formatoInvalido ? 'Não foi possível interpretar os alertas retornados pelo servidor.' : '')
        }
        aoTentar={aoAtualizar}
      />
      <section className="secao-oportunidades" aria-labelledby="titulo-oportunidades">
        <header className="cabecalho-secao">
          <div>
            <p className="sobretitulo">DA INFORMAÇÃO À AÇÃO</p>
            <h2 id="titulo-oportunidades">
              Sua próxima boa conversa <span>{disponivel ? selecionadas.length : '—'}</span>
            </h2>
            <p>Abra o cliente para conferir ciclos por fábrica, reposição e expansão de mix.</p>
          </div>
        </header>
        <FiltrosTipo
          rotulo="Tipo de oportunidade"
          opcoes={tipos}
          selecionada={tipo}
          aoSelecionar={definirTipo}
          contar={(opcao) =>
            opcao === 'Todas' ? filtradas.length : filtradas.filter((item) => item.tipo === opcao).length
          }
        />
        {disponivel &&
          (selecionadas.length ? (
            <div className="grade-oportunidades">
              {selecionadas.slice(0, limite).map((item) => (
                <CartaoOportunidade
                  key={item.id}
                  oportunidade={item}
                  cliente={item.cliente}
                  aoAbrirCliente={aoAbrirCliente}
                />
              ))}
            </div>
          ) : (
            <EstadoVazio
              titulo="Nenhum alerta nesta seleção"
              descricao="Ajuste os filtros ou consulte um cliente para conhecer seu histórico."
            />
          ))}
        {disponivel && selecionadas.length > limite && (
          <button className="botao-secundario mostrar-mais" onClick={() => definirLimite(limite + 12)}>
            Mostrar mais oportunidades
          </button>
        )}
      </section>
      <Cartao
        titulo="Quer olhar uma relação mais de perto?"
        descricao="Pesquise um cliente e veja o comparativo de faturamento e as recomendações disponíveis."
        className="atalho-clientes"
      >
        <button className="botao-secundario" onClick={aoVerClientes}>
          Consultar clientes
        </button>
        <p className="nota-disponibilidade">
          O faturamento consolidado e os totais gerais da carteira ainda não estão disponíveis. Os indicadores
          acima se referem apenas aos alertas recebidos.
        </p>
      </Cartao>
    </main>
  )
}
