import { useEstadoPagina } from '../servicos/estadoPaginas'
import { useState } from 'react'

import EstadoConsulta from '../componentes/EstadoConsulta'
import Seletor from '../componentes/Seletor'
import Cartao from '../componentes/Cartao'
import ListaProdutos from '../componentes/ListaProdutos'
import useDados from '../hooks/useDados'
import { solicitar } from '../servicos/api'
import { formatarMoeda } from '../servicos/formatacao'

export default function RelatorioRede({ fabricas }) {
  const [rede, definirRede] = useEstadoPagina('relatorioRede.rede', '')
  const [fabrica, definirFabrica] = useEstadoPagina('relatorioRede.fabrica', '')
  const [baixando, definirBaixando] = useState(false)
  const [erro, definirErro] = useState('')
  const redes = useDados('/relatorios/redes')
  const parametros = new URLSearchParams({ rede })
  if (fabrica) parametros.set('fabrica_id', fabrica)
  const caminho = `/relatorios/produtos-rede?${parametros}`
  const consulta = useDados(rede ? caminho : null)
  async function baixar() {
    definirBaixando(true); definirErro('')
    try {
      const pdf = await solicitar(`/relatorios/produtos-rede/pdf?${parametros}`, { formato: 'blob' })
      const url = URL.createObjectURL(pdf)
      const link = document.createElement('a')
      link.href = url; link.download = 'produtos-da-rede.pdf'
      document.body.appendChild(link); link.click(); link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (falha) { definirErro(falha.message) }
    finally { definirBaixando(false) }
  }
  return <>

    <Cartao titulo="Códigos comprados pela rede" descricao="Último pedido e último preço unitário por produto, considerando todos os CNPJs da rede.">
      <div className="filtros-comerciais faixa-filtros">
        <label>Rede de clientes<select aria-label="Rede de clientes" value={rede} disabled={baixando} onChange={(e) => { definirRede(e.target.value); definirErro('') }}>
          <option value="">Selecione uma rede</option>
          {redes.dados?.map((r) => <option key={r.nome} value={r.nome}>{r.nome} ({r.clientes} cadastros fiscais)</option>)}
        </select></label>
        <Seletor rotulo="Fábrica" todos="Todas as fábricas" opcoes={fabricas} valor={fabrica} aoMudar={definirFabrica} disabled={baixando} />
        <button className="botao-principal" disabled={!rede || consulta.carregando || !consulta.dados || baixando} onClick={baixar}>{baixando ? 'Gerando PDF…' : 'Baixar PDF'}</button>
      </div>
      <EstadoConsulta carregando={redes.carregando || consulta.carregando} erro={erro || redes.erro || consulta.erro} aoTentar={() => { definirErro(''); redes.tentarNovamente(); consulta.tentarNovamente() }} />
      {!redes.carregando && redes.dados?.length === 0 && <p>Não há redes cadastradas. Preencha a coluna Rede de clientes na importação.</p>}
      {consulta.dados && <>
        <p>{consulta.dados.clientes} cadastros fiscais · {consulta.dados.total} {consulta.dados.total === 1 ? 'código encontrado' : 'códigos encontrados'}.</p>
        {consulta.dados.total > 0 && <ListaProdutos key={`${rede}:${fabrica}`} produtos={consulta.dados.produtos} inicial={20} incremento={20}
          renderizarLista={(visiveis) => <div className="rolagem-tabela"><table aria-label="Códigos comprados pela rede"><thead><tr><th>Código</th><th>Produto</th><th>Fábrica</th><th>Último pedido</th><th>Último preço unitário</th><th>Pedido</th><th>Cliente da compra</th></tr></thead>
          <tbody>{visiveis.map((p) => <tr key={p.produto_id}><td>{p.sku}</td><td>{p.nome}</td><td>{p.fabrica}</td><td>{p.ultima_compra.split('-').reverse().join('/')}</td><td className="valor-numerico">{formatarMoeda(p.ultimo_preco)}</td><td>{p.pedido}</td><td>{p.cliente}</td></tr>)}</tbody></table></div>} />}
        <p className="nota-painel">A busca na lista filtra somente a exibição. O PDF inclui todos os códigos da rede e da fábrica selecionadas nos filtros acima.</p>
        {!consulta.dados.total && <p>Nenhum produto comprado com os filtros selecionados.</p>}
        <p className="nota-painel">{consulta.dados.pedidos_sem_itens} pedidos sem itens. Códigos e preços desses pedidos não estão disponíveis. O último preço pertence à última compra encontrada na rede, no histórico importado.</p>
      </>}
    </Cartao>
  </>
}
