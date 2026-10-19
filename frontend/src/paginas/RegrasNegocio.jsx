import { useRef, useState } from 'react'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import Cartao from '../componentes/Cartao'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Paginacao from '../componentes/Paginacao'
import useDados from '../hooks/useDados'
import { solicitar } from '../servicos/api'
import { dataLocal, formatarData } from '../servicos/formatacao'

const ufs = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ')
function inicial() { return { tipo: 'SUBSTITUICAO', fabrica_id: '', cliente_id: '', uf: '', codigo_antigo: '', codigo_novo: '', unificar_historico: true, excecoes_clientes: [], excecoes_vendedores: [], excecoes_clientes_detalhes: [], inicio: dataLocal(), fim: '', ativa: true, motivo: '' } }
function entrada(r) {
  return { tipo: r.tipo, fabrica_id: Number(r.fabrica_id), cliente_id: r.cliente_id ? Number(r.cliente_id) : null,
    uf: r.tipo === 'RESTRICAO' ? r.uf || null : null,
    codigo_antigo: r.tipo === 'SUBSTITUICAO' ? r.codigo_antigo : null,
    codigo_novo: r.tipo === 'SUBSTITUICAO' ? r.codigo_novo : null,
    unificar_historico: r.unificar_historico ?? true,
    excecoes_clientes: r.tipo === 'RESTRICAO' ? r.excecoes_clientes || [] : [],
    excecoes_vendedores: r.tipo === 'RESTRICAO' ? r.excecoes_vendedores || [] : [],
    inicio: r.inicio, fim: r.fim || null, ativa: r.ativa, motivo: r.motivo }
}
function situacao(r) {
  if (!r.ativa) return 'Desativada'
  if (r.inicio > dataLocal()) return 'Agendada'
  if (r.fim && r.fim < dataLocal()) return 'Encerrada'
  return 'Em vigor'
}

export default function RegrasNegocio({ fabricas = [], vendedores = [], gestor = false, aoAlterar }) {
  const [form, setForm] = useState(inicial)
  const [editando, setEditando] = useState(null)
  const [clienteNome, setClienteNome] = useState('')
  const [busca, setBusca] = useState('')
  const [termo, setTermo] = useState('')
  const [pagina, setPagina] = useState(1)
  const [versao, setVersao] = useState(0)
  const [pendente, setPendente] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const formulario = useRef(null)
  const lista = useDados(`/regras?pagina=${pagina}`, versao)
  const clientes = useDados(termo.length >= 2 ? `/comercial/clientes?termo=${encodeURIComponent(termo)}` : null)
  function mudar(campo, valor) { setForm((r) => ({ ...r, [campo]: valor })); setSucesso('') }
  function limpar() { setForm(inicial()); setEditando(null); setClienteNome(''); setBusca(''); setTermo('') }
  function editar(r) {
    setForm({ ...inicial(), ...r, cliente_id: r.cliente_id || '', uf: r.uf || '', fim: r.fim || '' })
    setEditando(r.id); setClienteNome(r.cliente || ''); setErro(''); setSucesso('')
    formulario.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  async function gravar(r, id = null) {
    setPendente(true); setErro(''); setSucesso('')
    try {
      await solicitar(id ? `/regras/${id}` : '/regras', { method: 'POST', body: entrada(r) })
      setVersao((v) => v + 1); aoAlterar?.()
      return true
    } catch (e) { setErro(e.message); return false }
    finally { setPendente(false) }
  }
  async function salvar(e) {
    e.preventDefault()
    if (await gravar(form, editando)) { limpar(); setPagina(1); setSucesso('Regra salva. Os próximos cálculos já consideram sua vigência.') }
  }
  async function alternar(r) {
    if (await gravar({ ...r, ativa: !r.ativa }, r.id)) {
      if (editando === r.id) limpar()
      setSucesso(r.ativa ? 'Regra desativada.' : 'Regra ativada conforme sua vigência.')
    }
  }
  return <main className="conteudo-painel pagina-regras" id="conteudo">
    <CabecalhoPagina titulo="Regras de negócio" descricao="Substituições de produtos e restrições comerciais por fábrica, estado ou cliente." />
    <p className="nota-painel">As regras orientam sugestões, recompra, abandono e inatividade. Pedidos, códigos e preços originais continuam preservados nos relatórios de vendas. Cada rede é um cliente comercial; regras para um cliente abrangem seus CNPJs.</p>
    {erro && <p role="alert">{erro}</p>}
    {sucesso && <p role="status">{sucesso}</p>}
    {gestor && <div ref={formulario}><Cartao titulo={editando ? `Editar regra #${editando}` : 'Nova regra'}>
      <form onSubmit={salvar}>
        <fieldset disabled={pendente} className="campos-regra">
          <div className="filtros-comerciais">
            <label>Tipo de regra<select value={form.tipo} onChange={(e) => mudar('tipo', e.target.value)}><option value="SUBSTITUICAO">Substituição de produto</option><option value="RESTRICAO">Restrição de venda da fábrica</option></select></label>
            <label>Fábrica<select required value={form.fabrica_id} onChange={(e) => mudar('fabrica_id', e.target.value)}><option value="">Selecione a fábrica</option>{fabricas.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}</select></label>
            <label>Início da vigência<input type="date" required value={form.inicio} onInput={(e) => mudar('inicio', e.currentTarget.value)} onChange={(e) => mudar('inicio', e.target.value)} /></label>
            <label>Fim da vigência (opcional)<input type="date" min={form.inicio} value={form.fim} onInput={(e) => mudar('fim', e.currentTarget.value)} onChange={(e) => mudar('fim', e.target.value)} /></label>
          </div>
          {form.tipo === 'SUBSTITUICAO' ? <>
            <div className="filtros-comerciais">
              <label>Código antigo<input required maxLength={150} value={form.codigo_antigo || ''} onChange={(e) => mudar('codigo_antigo', e.target.value)} /></label>
              <label>Código que substitui<input required maxLength={150} value={form.codigo_novo || ''} onChange={(e) => mudar('codigo_novo', e.target.value)} /></label>
            </div>
            <label className="opcao-rede"><input type="checkbox" checked={form.unificar_historico} onChange={(e) => mudar('unificar_historico', e.target.checked)} />Unificar também as compras anteriores ao início da vigência</label>
            <p className="nota-painel">Após o início da vigência, esta opção reúne também as compras antigas. Desmarcada, unifica apenas compras feitas a partir dessa data. Análises anteriores ao início da regra preservam a interpretação original.</p>
            <p className="nota-painel">Os dois produtos precisam estar importados na fábrica selecionada. O histórico e as quantidades são somados para recompra e abandono; as sugestões usam o código sucessor, sem recomendar novamente o equivalente já comprado. Use para itens equivalentes na mesma unidade de venda. A regra específica do cliente prevalece sobre a geral para o mesmo código.</p>
          </> : <>
            <label>Estado da restrição<select value={form.uf} onChange={(e) => mudar('uf', e.target.value)}><option value="">Todos os estados</option>{ufs.map((uf) => <option key={uf}>{uf}</option>)}</select></label>
            <p className="nota-painel">Retira a fábrica das sugestões e dos alertas de inatividade para os cadastros abrangidos. A UF vem do cadastro fiscal; se a rede tiver CNPJs em outros estados onde a venda é permitida, a relação comercial continua elegível por esses CNPJs.</p>
          </>}
          <div className="filtros-comerciais">
            <label>Aplicar ao cliente<select value={form.cliente_id} onChange={(e) => { const id = e.target.value; mudar('cliente_id', id); setClienteNome(clientes.dados?.itens.find((c) => String(c.id) === id)?.razao_social || '') }}>
              <option value="">Todos os clientes da fábrica</option>
              {form.cliente_id && <option value={form.cliente_id}>{clienteNome || `Cliente #${form.cliente_id}`}</option>}
              {clientes.dados?.itens.filter((c) => String(c.id) !== String(form.cliente_id)).map((c) => <option key={c.id} value={c.id}>{c.razao_social}</option>)}
            </select></label>
            <label>Buscar cliente<input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Nome, rede ou CNPJ" /></label>
            <button className="botao-secundario" type="button" disabled={busca.trim().length < 2} onClick={() => setTermo(busca.trim())}>Buscar cliente</button>
          </div>
          <EstadoConsulta carregando={clientes.carregando} erro={clientes.erro} aoTentar={clientes.tentarNovamente} />
          {clientes.dados?.total === 0 && <p>Nenhum cliente encontrado.</p>}
          {form.tipo === 'RESTRICAO' && <section>
            <h3>Exceções desta restrição</h3>
            <p className="nota-painel">A venda continua permitida se o cliente OU o vendedor estiver entre as exceções desta regra. Outras restrições independentes continuam valendo.</p>
            <label>Adicionar cliente com exceção<select value="" onChange={(e) => {
              const c = clientes.dados?.itens.find((item) => String(item.id) === e.target.value)
              if (c && !form.excecoes_clientes.includes(c.id)) setForm((r) => ({ ...r, excecoes_clientes: [...r.excecoes_clientes, c.id], excecoes_clientes_detalhes: [...r.excecoes_clientes_detalhes, { id: c.id, nome: c.razao_social }] }))
            }}><option value="">Use Buscar cliente acima e selecione o resultado</option>{clientes.dados?.itens.filter((c) => !form.excecoes_clientes.includes(c.id)).map((c) => <option key={c.id} value={c.id}>{c.razao_social}</option>)}</select></label>
            <ul>{form.excecoes_clientes_detalhes?.map((c) => <li key={c.id}>{c.nome} <button type="button" className="botao-texto" onClick={() => setForm((r) => ({ ...r, excecoes_clientes: r.excecoes_clientes.filter((id) => id !== c.id), excecoes_clientes_detalhes: r.excecoes_clientes_detalhes.filter((item) => item.id !== c.id) }))}>Remover exceção de {c.nome}</button></li>)}</ul>
            <p>Vendedores com exceção</p>
            <div className="filtros-comerciais">{vendedores.map((v) => <label className="opcao-rede" key={v.id}><input type="checkbox" checked={form.excecoes_vendedores.includes(v.id)} onChange={(e) => mudar('excecoes_vendedores', e.target.checked ? [...form.excecoes_vendedores, v.id] : form.excecoes_vendedores.filter((id) => id !== v.id))} />{v.nome}</label>)}</div>
            <p className="nota-painel">Nos alertas e sugestões, considera sempre o vendedor do último pedido do cliente ou rede, independentemente da fábrica, até a data analisada. Uma compra por outro vendedor altera essa referência nos próximos cálculos.</p>
          </section>}
          <label>Motivo / observação<textarea maxLength={1000} value={form.motivo} onChange={(e) => mudar('motivo', e.target.value)} /></label>
          <p className="nota-painel">{form.cliente_id ? `Escopo: ${clienteNome || 'cliente selecionado'}, incluindo seus CNPJs.` : 'Escopo: todos os clientes da fábrica.'}{form.tipo === 'RESTRICAO' ? ` Restrição em ${form.uf || 'todos os estados'}.` : ''}</p>
          <div className="filtros-comerciais"><button className="botao-secundario" type="submit">{pendente ? 'Salvando…' : editando ? 'Salvar alterações' : 'Cadastrar regra'}</button>{editando && <button type="button" className="botao-texto" onClick={limpar}>Cancelar edição</button>}</div>
        </fieldset>
      </form>
    </Cartao></div>}
    {!gestor && <p>Administradores e gestores podem cadastrar e editar regras.</p>}
    <Cartao titulo="Regras cadastradas">
      <p className="nota-painel">Para encerrar a aplicação a partir de uma data, informe o fim da vigência. Desativar retira a regra também dos cálculos de datas anteriores.</p>
      <EstadoConsulta carregando={lista.carregando} erro={lista.erro} aoTentar={lista.tentarNovamente} />
      {lista.dados?.total === 0 && <p>Nenhuma regra cadastrada. Os exemplos não foram incluídos automaticamente.</p>}
      <div className="rolagem-tabela"><table><thead><tr><th>Regra</th><th>Fábrica</th><th>Abrangência</th><th>Vigência</th><th>Situação</th>{gestor && <th>Ações</th>}</tr></thead><tbody>
        {lista.dados?.itens.map((r) => <tr key={r.id}><td><strong>{r.tipo === 'SUBSTITUICAO' ? `${r.codigo_antigo} → ${r.codigo_novo}` : `Venda restrita em ${r.uf || 'todos os estados'}`}</strong>{r.motivo && <p>{r.motivo}</p>}{r.excecoes_clientes_detalhes?.length > 0 && <p>Exceções de clientes: {r.excecoes_clientes_detalhes.map((c) => c.nome).join(', ')}</p>}{r.excecoes_vendedores_detalhes?.length > 0 && <p>Exceções de vendedores: {r.excecoes_vendedores_detalhes.map((v) => v.nome).join(', ')}</p>}</td><td>{r.fabrica}</td><td>{r.cliente || 'Todos os clientes'}{r.cliente && ' · CNPJs da rede'}</td><td>{formatarData(r.inicio)} a {r.fim ? formatarData(r.fim) : 'sem data final'}</td><td>{situacao(r)}</td>{gestor && <td><div className="acoes-regras"><button className="botao-texto" disabled={pendente} onClick={() => editar(r)}>Editar</button><button className="botao-texto" disabled={pendente} onClick={() => alternar(r)}>{r.ativa ? 'Desativar' : 'Ativar'}</button></div></td>}</tr>)}
      </tbody></table></div>
      {lista.dados && <Paginacao pagina={pagina} total={lista.dados.total} tamanho={30} aoMudar={setPagina} unidade="regras" />}
    </Cartao>
  </main>
}
