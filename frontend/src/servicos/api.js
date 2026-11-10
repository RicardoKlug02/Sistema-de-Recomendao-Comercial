const origem = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const chave = 'rioverde.sessao'

export function obterSessao() {
  try { return JSON.parse(sessionStorage.getItem(chave) || 'null') } catch { return null }
}
export function salvarSessao(sessao) {
  if (sessao) sessionStorage.setItem(chave, JSON.stringify(sessao))
  else sessionStorage.removeItem(chave)
}

export function montarCaminho(caminho, parametros = {}) {
  const busca = new URLSearchParams()
  for (const [nome, valor] of Object.entries(parametros))
    if (valor !== '' && valor !== null && valor !== undefined) busca.set(nome, valor)
  const texto = busca.toString()
  return texto ? `${caminho}?${texto}` : caminho
}

export async function solicitar(caminho, opcoes = {}) {
  const { tempoLimite = 90000, formato = 'json', signal, ...config } = opcoes
  const controlador = new AbortController()
  const cancelar = () => controlador.abort()
  if (signal?.aborted) cancelar()
  else signal?.addEventListener('abort', cancelar, { once: true })
  const temporizador = setTimeout(() => controlador.abort(), tempoLimite)
  const token = obterSessao()?.access_token
  const headers = new Headers(config.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (config.body && !(config.body instanceof FormData) && !(config.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
    config.body = JSON.stringify(config.body)
  }
  try {
    const resposta = await fetch(`${origem}/api/v1${caminho}`, { ...config, headers, signal: controlador.signal })
    const dados = resposta.ok && formato === 'blob' ? await resposta.blob() : await resposta.json().catch(() => null)
    if (!resposta.ok) {
      if (resposta.status === 401 && token) {
        salvarSessao(null)
        window.dispatchEvent(new Event('sessao-expirada'))
      }
      const detalhe = Array.isArray(dados?.detail) ? dados.detail.map((d) => d.msg).join('; ') : dados?.detail
      throw new Error(detalhe || `Falha na solicitação (HTTP ${resposta.status}).`)
    }
    return dados
  } catch (erro) {
    if (erro.name === 'AbortError') throw new Error('O servidor demorou para responder. Aguarde e tente novamente.', { cause: erro })
    if (erro instanceof TypeError) throw new Error('Não foi possível acessar a API. Verifique a conexão e o endereço configurado.', { cause: erro })
    throw erro
  } finally {
    clearTimeout(temporizador)
    signal?.removeEventListener('abort', cancelar)
  }
}

export async function baixarArquivo(caminho, nomeArquivo, opcoes = {}) {
  const arquivo = await solicitar(caminho, { ...opcoes, formato: 'blob' })
  const url = URL.createObjectURL(arquivo)
  const link = Object.assign(document.createElement('a'), { href: url, download: nomeArquivo })
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
