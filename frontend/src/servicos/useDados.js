import { useEffect, useState } from 'react'
import { solicitar } from './api'

export default function useDados(endpoint, versao = 0) {
  const [resultado, definirResultado] = useState({ chave: null, dados: null, erro: '' })
  const chave = `${endpoint}:${versao}`
  useEffect(() => {
    if (!endpoint) return
    let ativa = true
    solicitar(endpoint).then((dados) => {
      if (ativa) definirResultado({ chave, dados, erro: '' })
    }).catch((falha) => {
      if (ativa) definirResultado({ chave, dados: null, erro: falha.message })
    })
    return () => { ativa = false }
  }, [endpoint, chave])
  return resultado.chave === chave ? { ...resultado, carregando: false } : { dados: null, erro: '', carregando: !!endpoint }
}
