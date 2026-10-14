import { useState } from 'react'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import FiltroFabrica from '../componentes/comercial/FiltroFabrica'
import Cartao from '../componentes/Cartao'
import useDados from '../servicos/useDados'
import { solicitar } from '../servicos/api'
import { formatarMoeda } from '../servicos/dadosPainel'

export default function Relatorios({ fabricas }) {
  const [rede, definirRede] = useState('')
  const [fabrica, definirFabrica] = useState('')
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
  return <main className="conteudo-painel" id="conteudo">
    <CabecalhoPagina titulo="Relatórios" descricao="Histórico da rede para preparar sua próxima negociação." />
    <Cartao titulo="Códigos comprados pela rede" descricao="Último pedido e último preço unitário por produto, considerando todas as filiais da rede.">
      <div className="filtros-comerciais faixa-filtros">
        <label>Rede de clientes<select aria-label="Rede de clientes" value={rede} disabled={baixando} onChange={(e) => { definirRede(e.target.value); definirErro('') }}>
          <option value="">Selecione uma rede</option>
          {redes.dados?.map((r) => <option key={r.nome} value={r.nome}>{r.nome} ({r.clientes} estabelecimentos)</option>)}
        </select></label>
        <FiltroFabrica fabricas={fabricas} valor={fabrica} aoMudar={definirFabrica} disabled={baixando} />
        <button className="botao-principal" disabled={!rede || consulta.carregando || !consulta.dados || baixando} onClick={baixar}>{baixando ? 'Gerando PDF…' : 'Baixar PDF'}</button>
      </div>
      <EstadoConsulta carregando={redes.carregando || consulta.carregando} erro={erro || redes.erro || consulta.erro} />
      {!redes.carregando && redes.dados?.length === 0 && <p>Não há redes cadastradas. Preencha a coluna Rede de clientes na importação.</p>}
      {consulta.dados && <>
        <p>{consulta.dados.clientes} estabelecimentos · {consulta.dados.total} {consulta.dados.total === 1 ? 'código encontrado' : 'códigos encontrados'}.</p>
        <div className="rolagem-tabela"><table><thead><tr><th>Código</th><th>Produto</th><th>Fábrica</th><th>Último pedido</th><th>Último preço unitário</th><th>Pedido</th><th>Cliente da compra</th></tr></thead>
          <tbody>{consulta.dados.produtos.map((p) => <tr key={p.produto_id}><td>{p.sku}</td><td>{p.nome}</td><td>{p.fabrica}</td><td>{p.ultima_compra.split('-').reverse().join('/')}</td><td>{formatarMoeda(p.ultimo_preco)}</td><td>{p.pedido}</td><td>{p.cliente}</td></tr>)}</tbody></table></div>
        {!consulta.dados.total && <p>Nenhum produto comprado com os filtros selecionados.</p>}
        <p className="nota-painel">{consulta.dados.pedidos_sem_itens} pedidos sem itens. Códigos e preços desses pedidos não estão disponíveis. O último preço pertence à última compra encontrada na rede, no histórico importado.</p>
      </>}
    </Cartao>
  </main>
}
