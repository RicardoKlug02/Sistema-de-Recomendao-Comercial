import { beforeEach, describe, expect, test, vi } from 'vitest'
import { obterSessao, salvarSessao, solicitar } from '../../src/servicos/api'

const responder = (dados, status = 200) =>
  new Response(JSON.stringify(dados), { status, headers: { 'Content-Type': 'application/json' } })

beforeEach(() => {
  const armazenamento = new Map()
  vi.stubGlobal('sessionStorage', {
    getItem: (chave) => armazenamento.get(chave) ?? null,
    setItem: (chave, valor) => armazenamento.set(chave, valor),
    removeItem: (chave) => armazenamento.delete(chave),
  })
  vi.stubGlobal('window', new EventTarget())
  vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('Requisição sem resposta configurada no teste.') }))
})

describe('sessão', () => {
  test('salva, lê e remove a sessão', () => {
    salvarSessao({ access_token: 'token' })
    expect(obterSessao()).toEqual({ access_token: 'token' })
    salvarSessao(null)
    expect(obterSessao()).toBeNull()
  })

  test('sessão corrompida é tratada como ausente', () => {
    sessionStorage.setItem('rioverde.sessao', '{inválido')
    expect(obterSessao()).toBeNull()
  })
})

describe('solicitar', () => {
  test('usa o prefixo da API e serializa o corpo em JSON', async () => {
    fetch.mockResolvedValue(responder({ ok: true }))
    await solicitar('/regras', { method: 'POST', body: { nome: 'Regra' } })
    const [url, opcoes] = fetch.mock.calls[0]
    expect(url).toBe('/api/v1/regras')
    expect(opcoes.headers.get('Content-Type')).toBe('application/json')
    expect(opcoes.body).toBe('{"nome":"Regra"}')
  })

  test('envia o token como Bearer', async () => {
    salvarSessao({ access_token: 'abc' })
    fetch.mockResolvedValue(responder([]))
    await solicitar('/comercial/clientes')
    expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer abc')
  })

  test('401 com sessão encerra a sessão e avisa a aplicação', async () => {
    salvarSessao({ access_token: 'expirado' })
    const expirou = vi.fn()
    window.addEventListener('sessao-expirada', expirou)
    fetch.mockResolvedValue(responder({ detail: 'Token expirado' }, 401))
    await expect(solicitar('/auth/me')).rejects.toThrow('Token expirado')
    expect(obterSessao()).toBeNull()
    expect(expirou).toHaveBeenCalledOnce()
  })

  test('junta as mensagens de validação do FastAPI', async () => {
    fetch.mockResolvedValue(responder({ detail: [{ msg: 'Campo obrigatório' }, { msg: 'Valor inválido' }] }, 422))
    await expect(solicitar('/regras')).rejects.toThrow('Campo obrigatório; Valor inválido')
  })

  test('erro sem detalhe informa o status HTTP', async () => {
    fetch.mockResolvedValue(new Response('falha', { status: 500 }))
    await expect(solicitar('/regras')).rejects.toThrow('HTTP 500')
  })

  test('falha de rede vira mensagem para o usuário', async () => {
    fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(solicitar('/regras')).rejects.toThrow('Não foi possível acessar a API')
  })

  test('tempo limite cancela a requisição', async () => {
    fetch.mockImplementation((_, { signal }) => new Promise((_, rejeitar) =>
      signal.addEventListener('abort', () => rejeitar(new DOMException('Cancelado', 'AbortError')))))
    await expect(solicitar('/regras', { tempoLimite: 5 })).rejects.toThrow('O servidor demorou para responder')
  })

  test('formato blob devolve o arquivo', async () => {
    fetch.mockResolvedValue(new Response(new Blob(['%PDF']), { status: 200 }))
    const arquivo = await solicitar('/relatorios/pdf', { formato: 'blob' })
    expect(await arquivo.text()).toBe('%PDF')
  })
})
