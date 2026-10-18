import { useEffect, useState } from 'react'
import { solicitar } from '../servicos/api'

export default function useDados(endpoint, versao = 0) {
  const [resultado, definirResultado] = useState({ chave: null, dados: null, erro: '' })
  const chave = `${endpoint}:${versao}`
  useEffect(() => {
    if (!endpoint) return
    let ativa = true
    const controlador = new AbortController()
    solicitar(endpoint, { signal: controlador.signal })
      .then((dados) => ativa && definirResultado({ chave, dados, erro: '' }))
      .catch((falha) => ativa && definirResultado({ chave, dados: null, erro: falha.message }))
    return () => { ativa = false; controlador.abort() }
  }, [endpoint, chave])
  return resultado.chave === chave ? { ...resultado, carregando: false } : { dados: null, erro: '', carregando: !!endpoint }
}
