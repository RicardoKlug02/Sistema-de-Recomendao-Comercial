import { useCallback, useEffect, useState } from 'react'
import { solicitar } from '../servicos/api'

export default function useDados(endpoint, versao = 0) {
  const [resultado, definirResultado] = useState({ chave: null, dados: null, erro: '' })
  const [tentativa, definirTentativa] = useState(0)
  const tentarNovamente = useCallback(() => definirTentativa((v) => v + 1), [])
  const base = `${endpoint}:${versao}`
  const chave = `${base}:${tentativa}`
  useEffect(() => {
    if (!endpoint) return
    let ativa = true
    const controlador = new AbortController()
    solicitar(endpoint, { signal: controlador.signal }).then((dados) => {
      if (ativa) definirResultado({ chave, base, dados, erro: '' })
    }).catch((falha) => {
      if (ativa) definirResultado({ chave, base, dados: null, erro: falha.message })
    })
    return () => { ativa = false; controlador.abort() }
  }, [endpoint, chave, base])
  return resultado.chave === chave ? { ...resultado, carregando: false, tentarNovamente } : { dados: resultado.base === base ? resultado.dados : null, erro: '', carregando: !!endpoint, tentarNovamente }
}
