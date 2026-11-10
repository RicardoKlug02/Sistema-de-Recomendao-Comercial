import { useState } from 'react'
import Cartao from '../componentes/Cartao'
import EstadoConsulta from '../componentes/EstadoConsulta'
import Pagina from '../componentes/Pagina'
import Tabela from '../componentes/Tabela'
import useAcao from '../hooks/useAcao'
import useDados from '../hooks/useDados'
import { solicitar } from '../servicos/api'

export default function Usuarios() {
  const [versao, definirVersao] = useState(0)
  const aprovacao = useAcao()
  const usuarios = useDados('/auth/usuarios', versao)

  async function aprovar(id) {
    if (await aprovacao.executar(() => solicitar(`/auth/usuarios/${id}/aprovar`, { method: 'POST' }))) definirVersao((v) => v + 1)
  }

  return (
    <Pagina titulo="Usuários" descricao="Gerencie as solicitações de acesso da sua equipe.">
      <Cartao titulo="Aprovação de acesso">
        <EstadoConsulta carregando={usuarios.carregando} erro={aprovacao.erro || usuarios.erro} aoTentar={() => { aprovacao.definirErro(''); usuarios.tentarNovamente() }} />
        {usuarios.dados && (
          <Tabela colunas={['Nome', 'E-mail', 'Situação', 'Ação']}>
            {usuarios.dados.map((u) => (
              <tr key={u.id}><th>{u.nome}</th><td>{u.email}</td><td>{u.aprovado ? 'Aprovado' : 'Pendente'}</td>
                <td>{!u.aprovado && <button className="botao-secundario" disabled={aprovacao.executando} onClick={() => aprovar(u.id)}>Aprovar</button>}</td>
              </tr>
            ))}
          </Tabela>
        )}
      </Cartao>
    </Pagina>
  )
}
