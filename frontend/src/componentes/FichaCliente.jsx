import Cartao from './Cartao'
import CartaoIndicador from './CartaoIndicador'
import EstadoConsulta from './EstadoConsulta'
import RitmoCompras from './RitmoCompras'
import Tabela from './Tabela'
import useDados from '../hooks/useDados'
import { formatarMoeda } from '../servicos/formatacao'

function CartaoLista({ titulo, itens, chave, vazio, children: renderizar }) {
  return (
    <Cartao titulo={titulo}>
      {itens.length ? (
        <ul>
          {itens.map((item) => (
            <li key={item[chave]}>{renderizar(item)}</li>
          ))}
        </ul>
      ) : (
        <p>{vazio}</p>
      )}
    </Cartao>
  )
}

export default function FichaCliente({ clienteId, rede, fabrica, aoConsultarCadastro }) {
  const parametros = new URLSearchParams({ agrupar_rede: rede })
  if (fabrica) parametros.set('fabrica_id', fabrica)
  const ficha = useDados(`/clientes/${clienteId}?${parametros}`)
  const cliente = ficha.dados
  return (
    <>
      <EstadoConsulta carregando={ficha.carregando} erro={ficha.erro} />
      {cliente && (
        <>
          <section className="hero-cliente">
            <span className="sobretitulo">FICHA DO CLIENTE</span>
            <h2>{cliente.razao_social}</h2>
            <p>
              {cliente.grupo_economico || 'Cliente individual'} · {cliente.clientes_agrupados} cadastro(s) fiscal(is)
            </p>
          </section>
          <div className="grade-indicadores">
            <CartaoIndicador
              titulo="Valor comprado"
              valor={formatarMoeda(cliente.valor_comprado)}
              detalhe="Histórico completo"
            />
            <CartaoIndicador
              titulo="Pedidos emitidos"
              valor={cliente.pedidos_emitidos}
              detalhe="Inclui pedidos diretos de fábrica"
            />
          </div>
          <CartaoLista
            titulo="Cadastros fiscais do cliente"
            itens={cliente.cadastros_fiscais || []}
            chave="id"
            vazio="Nenhum cadastro fiscal informado."
          >
            {(c) => (
              <>
                {c.razao_social} · {c.cnpj_cpf || 'Documento não informado'}
                {rede && (
                  <button className="botao-texto" onClick={() => aoConsultarCadastro(c.id)}>
                    Consultar este CNPJ
                  </button>
                )}
              </>
            )}
          </CartaoLista>
          <RitmoCompras ritmo={cliente.ritmo_compras} produtos={cliente.comparacao_produtos || []} />
          <Cartao titulo="Fábricas e inatividade">
            <Tabela colunas={['Fábrica', 'Última compra', 'Data limite', 'Status']}>
              {cliente.resumo_fabricas.map((f) => (
                <tr key={f.fabrica_id}>
                  <th>{f.fabrica}</th>
                  <td>{f.ultima_compra}</td>
                  <td>{f.data_limite_inatividade}</td>
                  <td>{f.status}</td>
                </tr>
              ))}
            </Tabela>
          </Cartao>
          <div className="grade-resumos">
            <CartaoLista
              titulo="Reposição de produtos"
              itens={cliente.sugestoes_reposicao}
              chave="produto_id"
              vazio="Nenhuma reposição identificada neste momento."
            >
              {(p) => `Código ${p.sku} · ${p.nome}: ${p.status} · volume habitual ${p.volume_habitual}`}
            </CartaoLista>
            <CartaoLista
              titulo="Produtos em abandono"
              itens={cliente.produtos_em_abandono}
              chave="produto_id"
              vazio="Nenhum abandono identificado."
            >
              {(p) => `Código ${p.sku} · ${p.nome}: ${p.dias_parado} dias sem comprar.`}
            </CartaoLista>
            <CartaoLista
              titulo="Completar o mix"
              itens={cliente.sugestoes_expansao_mix}
              chave="produto_id"
              vazio="Ainda não há histórico semelhante suficiente para sugerir produtos."
            >
              {(p) => (
                <>
                  <strong>
                    Código {p.sku} · {p.nome}
                  </strong>
                  <p>
                    {p.motivo} · volume sugerido: {p.volume_sugerido_unidades}
                  </p>
                </>
              )}
            </CartaoLista>
            <CartaoLista
              titulo="Sugestões de fábricas"
              itens={cliente.sugestoes_fabricas}
              chave="id"
              vazio="Nenhuma sugestão de nova fábrica com o histórico disponível."
            >
              {(f) => (
                <>
                  <strong>{f.nome}</strong>
                  <p>{f.motivo}</p>
                </>
              )}
            </CartaoLista>
          </div>
          <p className="nota-painel">
            Restrições e substituições vigentes são aplicadas aos ciclos e às sugestões. Os valores históricos são
            preservados. Inatividade de fábrica: 90 dias. O ciclo de reposição utiliza as datas de compra do histórico.
          </p>
        </>
      )}
    </>
  )
}
