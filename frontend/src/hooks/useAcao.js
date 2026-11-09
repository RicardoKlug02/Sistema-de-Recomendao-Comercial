import { useCallback, useState } from 'react'

export default function useAcao() {
  const [executando, definirExecutando] = useState(false)
  const [erro, definirErro] = useState('')
  const executar = useCallback(async (acao) => {
    definirExecutando(true)
    definirErro('')
    try { await acao(); return true }
    catch (falha) { definirErro(falha.message); return false }
    finally { definirExecutando(false) }
  }, [])
  return { executar, executando, erro, definirErro }
}
