import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import useDados from '../servicos/useDados'
import { solicitar } from '../servicos/api'
export default function Usuarios() {
  const [versao, definirVersao] = useState(0)
  const [erro, definirErro] = useState('')
  const [pendente, definirPendente] = useState(null)
  const dados = useDados('/auth/usuarios', versao)
  async function aprovar(id) {
    definirPendente(id); definirErro('')
    try { await solicitar(`/auth/usuarios/${id}/aprovar`, { method: 'POST' }); definirVersao((v) => v + 1) }
    catch (falha) { definirErro(falha.message) }
    finally { definirPendente(null) }
  }
  return <main className="conteudo-painel"><header className="cabecalho-painel"><h1>Usuários</h1></header><Cartao titulo="Aprovação de acesso">
    {(erro || dados.erro) && <p role="alert">{erro || dados.erro}</p>}
    {dados.carregando ? <p role="status">Carregando…</p> : <div className="rolagem-tabela"><table><thead><tr><th>Nome</th><th>E-mail</th><th>Situação</th><th>Ação</th></tr></thead>
      <tbody>{dados.dados?.map((u) => <tr key={u.id}><th>{u.nome}</th><td>{u.email}</td><td>{u.aprovado ? 'Aprovado' : 'Pendente'}</td><td>{!u.aprovado && <button className="botao-secundario" disabled={pendente !== null} onClick={() => aprovar(u.id)}>Aprovar</button>}</td></tr>)}</tbody>
    </table></div>}</Cartao></main>
}
