import { useState } from 'react'
import { baixarArquivo } from '../../servicos/api'
import useAcao from '../../hooks/useAcao'
import { rotuloProduto } from '../../servicos/formatacao'

export default function ExportarVisita({ cliente, rede, fabrica }) {
  const [abandono, setAbandono] = useState(true)
  const [recompra, setRecompra] = useState(true)
  const [precos, setPrecos] = useState(false)
  const [busca, setBusca] = useState('')
  const [limite, setLimite] = useState(20)
  const [excluidos, setExcluidos] = useState(new Set())
  const [sucesso, setSucesso] = useState('')
  const acao = useAcao()
  const produtos = [...new Map([
    ...(abandono ? cliente.produtos_em_abandono : []),
    ...(recompra ? cliente.sugestoes_reposicao : []),
  ].map(p => [p.produto_id, p])).values()]
  const selecionados = produtos.filter(p => !excluidos.has(p.produto_id))
  const filtrados = produtos.filter(p => `${p.sku} ${p.nome} ${p.fabrica}`.toLocaleLowerCase('pt-BR').includes(busca.toLocaleLowerCase('pt-BR')))
  function marcar(id) {
    setSucesso('')
    setExcluidos(antes => { const novo = new Set(antes); if (novo.has(id)) novo.delete(id); else novo.add(id); return novo })
  }
  async function exportar(e) {
    e.preventDefault(); setSucesso('')
    const ok = await acao.executar(() => baixarArquivo(`/clientes/${cliente.cliente_id}/visita.pdf`, `preparacao-visita-${cliente.cliente_id}.pdf`, {
      method: 'POST', body: { agrupar_rede: rede, fabrica_id: fabrica ? Number(fabrica) : null,
        abandono, recompra, mostrar_precos: precos, produtos_ids: selecionados.map(p => p.produto_id) },
    }))
    if (ok) setSucesso('PDF gerado. Confira o arquivo nos downloads.')
  }
  return <details className="nota-painel preparacao-visita">
    <summary>Preparar visita e exportar PDF</summary>
    <p>Usa a rede/CNPJ e a fábrica selecionados nesta ficha. Produtos com recompra não confirmada ficam fora do relatório.</p>
    <form onSubmit={exportar}>
      <fieldset disabled={acao.executando}>
        <legend>Conteúdo do relatório</legend>
        <div className="opcoes-pdf">
          <label><input type="checkbox" checked={abandono} onChange={e => { setAbandono(e.target.checked); setSucesso('') }} /> Itens em abandono</label>
          <label><input type="checkbox" checked={recompra} onChange={e => { setRecompra(e.target.checked); setSucesso('') }} /> Sugestões de recompra</label>
          <label><input type="checkbox" checked={precos} onChange={e => setPrecos(e.target.checked)} /> Incluir último preço pago</label>
        </div>
        <p>{selecionados.length} de {produtos.length} produtos selecionados. A busca limita a lista exibida; o PDF inclui todos os selecionados.</p>
        <label>Buscar produto para o PDF<input value={busca} onChange={e => { setBusca(e.target.value); setLimite(20) }} /></label>
        <div className="filtros-comerciais">
          <button type="button" className="botao-secundario" onClick={() => { setExcluidos(new Set()); setSucesso('') }}>Selecionar todos</button>
          <button type="button" className="botao-secundario" onClick={() => { setExcluidos(new Set(produtos.map(p => p.produto_id))); setSucesso('') }}>Desmarcar todos</button>
        </div>
        <ul>{filtrados.slice(0, limite).map(p => <li key={p.produto_id}>
          <label><input type="checkbox" checked={!excluidos.has(p.produto_id)} onChange={() => marcar(p.produto_id)} /> {rotuloProduto(p)} · {p.nome}</label>
        </li>)}</ul>
        {filtrados.length > limite && <button type="button" className="botao-secundario" onClick={() => setLimite(n => n + 20)}>Mostrar mais produtos</button>}
        {!produtos.length && <p>Nenhum produto disponível para as seções selecionadas.</p>}
        <button className="botao-principal" disabled={!selecionados.length}>{acao.executando ? 'Gerando PDF…' : 'Baixar preparação da visita em PDF'}</button>
      </fieldset>
    </form>
    {acao.erro && <p role="alert">{acao.erro}</p>}
    {sucesso && <p role="status">{sucesso}</p>}
  </details>
}
