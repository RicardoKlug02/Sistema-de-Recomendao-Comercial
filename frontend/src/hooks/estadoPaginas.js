import { createContext, useContext, useEffect, useRef, useState } from 'react'

export const MemoriaPaginas = createContext(null)

export function useEstadoPagina(chave, inicial, priorizarInicial = false) {
  const memoria = useContext(MemoriaPaginas)
  const [valor, definir] = useState(() => !priorizarInicial && memoria?.has(chave) ? memoria.get(chave) : typeof inicial === 'function' ? inicial() : inicial)
  useEffect(() => { memoria?.set(chave, valor) }, [memoria, chave, valor])
  return [valor, definir]
}

export function useRolagemPagina(chave, pronto, ativa = true) {
  const memoria = useContext(MemoriaPaginas)
  const restaurou = useRef(false)
  const posicao = useRef(memoria?.get(`rolagem:${chave}`) || 0)
  useEffect(() => {
    if (!ativa) return
    const registrar = () => { if (restaurou.current) posicao.current = window.scrollY }
    window.addEventListener('scroll', registrar, { passive: true })
    return () => { window.removeEventListener('scroll', registrar); memoria?.set(`rolagem:${chave}`, posicao.current) }
  }, [chave, memoria, ativa])
  useEffect(() => {
    if (!ativa) { restaurou.current = false; return }
    if (!pronto || restaurou.current) return
    const quadro = requestAnimationFrame(() => { window.scrollTo(0, posicao.current); restaurou.current = true })
    return () => cancelAnimationFrame(quadro)
  }, [pronto, ativa])
}
