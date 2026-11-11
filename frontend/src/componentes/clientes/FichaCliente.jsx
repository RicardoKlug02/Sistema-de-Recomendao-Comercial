import Cartao from '../Cartao'
import CartaoIndicador from '../CartaoIndicador'
import EstadoConsulta from '../EstadoConsulta'
import Tabela from '../Tabela'
import ListaProdutos from './ListaProdutos'
import RitmoCompras from './RitmoCompras'
import ExportarVisita from './ExportarVisita'
import OrigemInformacao from '../OrigemInformacao'
import useDados from '../../hooks/useDados'
import { montarCaminho } from '../../servicos/api'
import { formatarMoeda, formatarData, rotuloProduto } from '../../servicos/formatacao'

function ListaOuVazio({ itens, vazio, children }) {
  return itens.length ? children : <p>{vazio}</p>
}

export default function FichaCliente({ clienteId, rede, fabrica, aoConsultarCadastro }) {
  const ficha = useDados(montarCaminho(`/clientes/${clienteId}`, { agrupar_rede: rede, fabrica_id: fabrica }))
  const cliente = ficha.dados
  return <>
    <EstadoConsulta erro={ficha.erro} carregando={ficha.carregando} aoTentar={ficha.tentarNovamente} />
    {cliente && <>
      <section className="hero-cliente">
        <span className="sobretitulo">FICHA DO CLIENTE</span>
        <h2>{cliente.razao_social}</h2>
        <p>{cliente.grupo_economico || 'Cliente individual'} · {cliente.clientes_agrupados} cadastro(s) fiscal(is)</p>
      </section>
      <nav className="atalhos-ficha" aria-label="Atalhos da ficha">
        <a href="#ficha-reposicao">Recomprar</a>
        <a href="#ficha-abandono">Recuperar produtos</a>
        <a href="#ficha-mix">Ampliar mix</a>
        <a href="#ficha-fabricas">Ver fábricas</a>
      </nav>
      <ExportarVisita key={`${clienteId}:${rede}:${fabrica}`} cliente={cliente} rede={rede} fabrica={fabrica} />
      {cliente.origem && <details className="nota-painel">
        <summary>Histórico utilizado e origem dos dados</summary>
        <p>Fonte: {cliente.origem.fonte}. Posição em {formatarData(cliente.origem.referencia)}.
          {' '}Escopo: {cliente.origem.escopo}. Rede cadastrada: {cliente.grupo_economico || 'Nenhuma — este CNPJ é analisado individualmente'}.
          {' '}Histórico de {formatarData(cliente.origem.inicio)} até {formatarData(cliente.origem.fim)}.</p>
        <p>O agrupamento usa o cadastro atual da rede, inclusive para pedidos antigos. Compras em CNPJs sem vínculo cadastrado não são somadas automaticamente.</p>
        <OrigemInformacao pedidos={cliente.origem.pedidos_sem_itens} titulo="Pedidos sem itens registrados na base" />
        <OrigemInformacao pedidos={cliente.origem.ajustes_comissionados} titulo="Ajustes comissionados: valor sem nova compra" />
      </details>}
      <div className="grade-indicadores">
        <CartaoIndicador titulo="Faturamento comissionado" valor={formatarMoeda(cliente.valor_comprado)}
          detalhe={fabrica ? 'Histórico da fábrica selecionada, com ajustes' : 'Histórico de todas as fábricas, com ajustes'} />
        <CartaoIndicador titulo="Pedidos de compra" valor={cliente.pedidos_emitidos} detalhe="Ajustes sem nova compra não entram na contagem" />
      </div>
      <Cartao titulo="Cadastros fiscais do cliente">
        <ul className="lista-clientes">{cliente.cadastros_fiscais?.map((c) => <li key={c.id}>
          <span>{c.razao_social} · {c.cnpj_cpf || 'Documento não informado'}</span>
          {rede && <button type="button" className="botao-secundario" onClick={() => aoConsultarCadastro(c.id)}>Consultar este CNPJ</button>}
        </li>)}</ul>
      </Cartao>
      <RitmoCompras ritmo={cliente.ritmo_compras} produtos={cliente.comparacao_produtos || []} />
      <Cartao id="ficha-fabricas" titulo="Fábricas e inatividade">
        <Tabela className="tabela-fabricas" colunas={['Fábrica', 'Última compra', 'Data limite', 'Status', 'Ritmo de recompra']}>
          {cliente.resumo_fabricas.map((f) => (
            <tr key={f.fabrica_id}>
              <th>{f.fabrica}</th>
              <td data-rotulo="Última compra">{f.ultima_compra}<OrigemInformacao origem={f.origem} titulo="Ver última compra" /></td>
              <td data-rotulo="Data limite">{f.data_limite_inatividade}</td>
              <td data-rotulo="Situação"><span className={`etiqueta ${f.situacao_atividade === 'Inativa' ? 'etiqueta-alerta' : 'etiqueta-neutra'}`}>{f.situacao_atividade}</span></td>
              <td data-rotulo="Ritmo de recompra">{f.situacao_recompra}</td>
            </tr>
          ))}
        </Tabela>
        <details className="entenda-indicador"><summary>Entenda este indicador</summary><p>A fábrica fica inativa a partir de 90 dias sem compra. A recompra pode estar atrasada antes disso, conforme o intervalo médio do histórico. São situações diferentes.</p></details>
      </Cartao>
      <div className="grade-resumos">
        <Cartao id="ficha-reposicao" titulo="Reposição de produtos">
          <ListaOuVazio itens={cliente.sugestoes_reposicao} vazio="Nenhuma reposição identificada neste momento.">
            <ListaProdutos produtos={cliente.sugestoes_reposicao} renderizarItem={(p) => (
              <li key={p.produto_id}><strong>{rotuloProduto(p)}</strong><br />{p.nome}: {p.status} · volume habitual {p.volume_habitual}<OrigemInformacao origem={p.origem} /></li>
            )} />
          </ListaOuVazio>
        </Cartao>
        <Cartao id="ficha-abandono" titulo="Produtos em abandono">
          {cliente.produtos_sem_confirmacao?.length > 0 && <section aria-label="Produtos com recompra não confirmada">
            <h3>Recompra não confirmada</h3>
            <p>Há pedidos posteriores sem itens registrados na base. Isso pode ser uma venda sem detalhamento ou uma importação incompleta. Confira os pedidos abaixo. Estes produtos não são contados como abandono confirmado.</p>
            <ListaProdutos produtos={cliente.produtos_sem_confirmacao} renderizarItem={(p) => <li key={p.produto_id}><strong>{rotuloProduto(p)}</strong><br />{p.nome}
              <p>Última compra conhecida: {formatarData(p.ultima_compra_conhecida)}.</p>
              <OrigemInformacao pedidos={p.pedidos_sem_itens} titulo="Ver pedidos que impedem confirmar a recompra" />
              <OrigemInformacao origem={p.origem} />
            </li>} />
          </section>}
          <section aria-label="Produtos com abandono confirmado">
          <h3>Abandono confirmado</h3>
          <ListaOuVazio itens={cliente.produtos_em_abandono} vazio="Nenhum abandono identificado.">
            <ListaProdutos produtos={cliente.produtos_em_abandono} renderizarItem={(p) => (
              <li key={p.produto_id}><strong>{rotuloProduto(p)}</strong><br />{p.nome}: {p.dias_parado} dias sem compra conhecida.
                <p>{p.total_vezes_comprado} datas de compra · ciclo médio de {p.ciclo_habitual} dias.</p>
                <OrigemInformacao origem={p.origem} />
              </li>
            )} />
          </ListaOuVazio>
          </section>
          <details className="entenda-indicador"><summary>Como o abandono é identificado?</summary>
            <p>Pelo menos 60 dias sem compra, mais de 2,5 vezes o ciclo médio e no mínimo três datas de compra. Pedidos sem itens podem impedir a confirmação.</p>
          </details>
        </Cartao>
        <Cartao id="ficha-mix" titulo="Completar o mix">
          <details className="entenda-indicador"><summary>Entenda as recomendações</summary><p>As sugestões usam compras de redes com histórico semelhante e respeitam as regras comerciais. Afinidade é uma pontuação de ordenação, não uma probabilidade de venda. Confira o contexto comercial antes de oferecer.</p></details>
          <ListaOuVazio itens={cliente.sugestoes_expansao_mix} vazio="Ainda não há histórico semelhante suficiente para sugerir produtos.">
            <ListaProdutos produtos={cliente.sugestoes_expansao_mix} renderizarItem={(p) => (
              <li key={p.produto_id}><strong>{rotuloProduto(p)}</strong><p>{p.nome}</p><p>Encontrado em históricos de compra semelhantes. Confira se faz sentido para este cliente.</p></li>
            )} />
          </ListaOuVazio>
        </Cartao>
        <Cartao titulo="Sugestões de fábricas">
          <ListaOuVazio itens={cliente.sugestoes_fabricas} vazio="Nenhuma sugestão de nova fábrica com o histórico disponível.">
            <ul>{cliente.sugestoes_fabricas.map((f) => <li key={f.id}><strong>{f.nome}</strong><p>{f.motivo}</p></li>)}</ul>
          </ListaOuVazio>
        </Cartao>
      </div>
      <p className="nota-painel">
        Restrições e substituições vigentes são aplicadas aos ciclos e às sugestões. Os valores históricos são preservados.
        Inatividade de fábrica: 90 dias. O ciclo de reposição utiliza as datas de compra do histórico.
      </p>
    </>}
  </>
}
