import { useState } from 'react'
import CabecalhoPagina from '../componentes/CabecalhoPagina'
import Cartao from '../componentes/Cartao'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Tabela from '../componentes/Tabela'
import useDados from '../hooks/useDados'
import { solicitar } from '../servicos/api'

export default function Usuarios() {
  const [versao, definirVersao] = useState(0)
  const [erro, definirErro] = useState('')
  const [aprovando, definirAprovando] = useState(false)
  const usuarios = useDados('/auth/usuarios', versao)

  async function aprovar(id) {
    definirAprovando(true)
    definirErro('')
    try {
      await solicitar(`/auth/usuarios/${id}/aprovar`, { method: 'POST' })
      definirVersao((v) => v + 1)
    } catch (falha) {
      definirErro(falha.message)
    } finally {
      definirAprovando(false)
    }
  }

  return (
    <main className="conteudo-painel">
      <CabecalhoPagina titulo="Usuários" descricao="Gerencie as solicitações de acesso da sua equipe." />
      <Cartao titulo="Aprovação de acesso">
        <EstadoConsulta carregando={usuarios.carregando} erro={erro || usuarios.erro} aoTentar={() => { definirErro(''); usuarios.tentarNovamente() }} />
        {usuarios.dados && (
          <Tabela colunas={['Nome', 'E-mail', 'Situação', 'Ação']}>
            {usuarios.dados.map((u) => (
              <tr key={u.id}>
                <th>{u.nome}</th>
                <td>{u.email}</td>
                <td>{u.aprovado ? 'Aprovado' : 'Pendente'}</td>
                <td>
                  {!u.aprovado && (
                    <button className="botao-secundario" disabled={aprovando} onClick={() => aprovar(u.id)}>
                      Aprovar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </Tabela>
        )}
      </Cartao>
    </main>
  )
}
