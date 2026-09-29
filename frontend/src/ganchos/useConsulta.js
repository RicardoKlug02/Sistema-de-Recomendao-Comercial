import { useEffect, useState } from 'react'
import { solicitarApi } from '../servicos/api'

// Cada resposta pertence a uma consulta; buscas antigas não substituem a seleção atual.
export default function useConsulta(caminho, versao = 0) {
  const [estado, definirEstado] = useState(null)
  const chave = caminho ? `${versao}:${caminho}` : null
  useEffect(() => {
    if (!caminho) return
    const controle = new AbortController()
    const atraso = setTimeout(() => {
      solicitarApi(caminho, { signal: controle.signal })
        .then((dados) => {
          if (!controle.signal.aborted) definirEstado({ chave, dados })
        })
        .catch((erro) => {
          if (!controle.signal.aborted) definirEstado({ chave, erro: erro.message })
        })
    }, 250)
    return () => {
      clearTimeout(atraso)
      controle.abort()
    }
  }, [caminho, chave])
  const atual = estado?.chave === chave ? estado : null
  return { dados: atual?.dados ?? null, erro: atual?.erro || '', carregando: Boolean(chave && !atual) }
}
