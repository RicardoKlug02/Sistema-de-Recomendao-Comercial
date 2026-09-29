const origemRender = 'https://sistema-de-recomendao-comercial.onrender.com'
const enderecoApi = (
  import.meta.env?.VITE_API_URL || (import.meta.env?.DEV ? '/api/v1' : `${origemRender}/api/v1`)
).replace(/\/$/, '')
const chaveSessao = 'rio-verde-sessao'

export function obterSessao() {
  try {
    const sessao = JSON.parse(sessionStorage.getItem(chaveSessao))
    return sessao?.token && sessao?.usuario?.email ? sessao : null
  } catch {
    return null
  }
}
export const guardarSessao = (sessao) => sessionStorage.setItem(chaveSessao, JSON.stringify(sessao))
export const encerrarSessao = () => sessionStorage.removeItem(chaveSessao)

// O prazo maior acomoda a inicialização do Render sem repetir cargas automaticamente.
export async function solicitarApi(caminho, { publico = false, prazo = 90000, signal, ...opcoes } = {}) {
  const cabecalhos = new Headers(opcoes.headers)
  const sessao = obterSessao()
  if (!publico && sessao) cabecalhos.set('Authorization', `Bearer ${sessao.token}`)
  const controle = new AbortController()
  const cancelar = () => controle.abort()
  signal?.addEventListener('abort', cancelar, { once: true })
  if (signal?.aborted) controle.abort()
  let expirou = false
  const limite = setTimeout(() => {
    expirou = true
    controle.abort()
  }, prazo)
  try {
    const resposta = await fetch(`${enderecoApi}${caminho}`, {
      ...opcoes,
      headers: cabecalhos,
      signal: controle.signal,
    })
    const dados = await resposta.json().catch(() => null)
    if (!resposta.ok) {
      if (resposta.status === 401 && !publico) {
        encerrarSessao()
        window.dispatchEvent(new Event('sessao-expirada'))
      }
      const detalhe = dados?.detail
      const mensagem =
        typeof detalhe === 'string'
          ? detalhe
          : Array.isArray(detalhe)
            ? detalhe.map((item) => item.msg).join(' ')
            : 'O servidor não conseguiu concluir a solicitação. Tente novamente.'
      const erro = new Error(mensagem)
      erro.status = resposta.status
      throw erro
    }
    if (dados === null) throw new Error('O servidor retornou uma resposta inesperada. Tente novamente.')
    return dados
  } catch (erro) {
    if (expirou)
      throw new Error(
        opcoes.method === 'POST' && caminho === '/cargas/excel'
          ? 'A importação demorou além do esperado. O servidor pode continuar processando. Confira os clientes antes de reenviar os arquivos.'
          : 'O servidor demorou para responder. Ele pode estar iniciando; tente novamente em alguns instantes.',
        { cause: erro },
      )
    if (erro.name === 'AbortError' || erro.status || !(erro instanceof TypeError)) throw erro
    throw new Error(
      'Não foi possível conectar ao servidor no Render. Confira sua conexão e tente novamente.',
      { cause: erro },
    )
  } finally {
    clearTimeout(limite)
    signal?.removeEventListener('abort', cancelar)
  }
}
