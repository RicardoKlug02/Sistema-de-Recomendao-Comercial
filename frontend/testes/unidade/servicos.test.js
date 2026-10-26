import { beforeEach, describe, expect, test, vi } from 'vitest'
import { obterSessao } from '../../src/servicos/api'
import { ehGestor, entrar, registrar, validarEmail } from '../../src/servicos/autenticacao'
import { formatarData, formatarDataHora, formatarMoeda } from '../../src/servicos/formatacao'
import { importarArquivos } from '../../src/servicos/importacao'

const responder = (dados, status = 200) =>
  new Response(JSON.stringify(dados), { status, headers: { 'Content-Type': 'application/json' } })
const planilha = (nome, conteudo = 'dados') => new File([conteudo], nome)

beforeEach(() => {
  const armazenamento = new Map()
  vi.stubGlobal('sessionStorage', {
    getItem: (chave) => armazenamento.get(chave) ?? null,
    setItem: (chave, valor) => armazenamento.set(chave, valor),
    removeItem: (chave) => armazenamento.delete(chave),
  })
  vi.stubGlobal('window', new EventTarget())
  vi.stubGlobal('fetch', vi.fn())
})

describe('autenticação', () => {
  test('login usa formulário OAuth2 e guarda a sessão sem a senha', async () => {
    fetch.mockResolvedValue(responder({
      access_token: 'token-teste', usuario_nome: 'Pessoa', usuario_email: 'pessoa@exemplo.com', usuario_perfil: 'admin',
    }))
    const usuario = await entrar({ email: ' pessoa@exemplo.com ', senha: 'senha-teste' })
    const [url, opcoes] = fetch.mock.calls[0]
    expect(url).toMatch(/\/api\/v1\/auth\/login$/)
    expect(opcoes.body.get('username')).toBe('pessoa@exemplo.com')
    expect(opcoes.headers.has('Authorization')).toBe(false)
    expect(usuario).toEqual({ nome: 'Pessoa', email: 'pessoa@exemplo.com', perfil: 'admin' })
    expect(obterSessao().access_token).toBe('token-teste')
    expect(JSON.stringify(obterSessao())).not.toContain('senha-teste')
  })

  test('erro de login mantém a mensagem do servidor e não cria sessão', async () => {
    fetch.mockResolvedValue(responder({ detail: 'Cadastro pendente de aprovação.' }, 401))
    await expect(entrar({ email: 'pessoa@exemplo.com', senha: 'incorreta' })).rejects.toThrow('pendente de aprovação')
    expect(obterSessao()).toBeNull()
  })

  test('cadastro envia nome, e-mail e senha em JSON', async () => {
    fetch.mockResolvedValue(responder({ mensagem: 'Aguarde aprovação.' }))
    await registrar({ nome: 'Pessoa', email: 'pessoa@exemplo.com', senha: '123456' })
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ nome: 'Pessoa', email: 'pessoa@exemplo.com', senha: '123456' })
  })

  test('valida e-mail e perfil de gestor', () => {
    expect(validarEmail('')).toBe('Informe seu e-mail.')
    expect(validarEmail('pessoa@')).toBe('Informe um e-mail válido.')
    expect(validarEmail('pessoa@exemplo.com')).toBe('')
    expect(ehGestor({ perfil: 'gestor' })).toBe(true)
    expect(ehGestor({ perfil: 'vendedor' })).toBe(false)
  })
})

describe('importação', () => {
  test('conferência envia as duas planilhas sem gravar', async () => {
    fetch.mockResolvedValue(responder({ token: 'conferencia' }))
    await importarArquivos(planilha('pedidos.xls'), planilha('itens.xlsx'))
    const [url, opcoes] = fetch.mock.calls[0]
    expect(url).toMatch(/\/cargas\/conferir$/)
    expect([...opcoes.body.keys()]).toEqual(['arquivo_cabecalho', 'arquivo_itens'])
    expect(opcoes.headers.has('Content-Type')).toBe(false)
  })

  test('confirmação envia o token da conferência', async () => {
    fetch.mockResolvedValue(responder({ mensagem: 'Importação concluída.' }))
    await importarArquivos(planilha('pedidos.xls'), planilha('itens.xlsx'), 'conferencia')
    const [url, opcoes] = fetch.mock.calls[0]
    expect(url).toMatch(/\/cargas\/excel$/)
    expect(opcoes.body.get('token_conferencia')).toBe('conferencia')
  })

  test('arquivos inválidos são bloqueados antes do envio', async () => {
    await expect(importarArquivos(null, planilha('itens.xlsx'))).rejects.toThrow('Selecione as duas planilhas.')
    await expect(importarArquivos(planilha('pedidos.txt'), planilha('itens.xlsx'))).rejects.toThrow('XLS ou XLSX')
    await expect(importarArquivos(planilha('pedidos.xls', ''), planilha('itens.xlsx'))).rejects.toThrow('10 MB')
    expect(fetch).not.toHaveBeenCalled()
  })
})

describe('formatação', () => {
  test('formata moeda, datas e valores ausentes', () => {
    expect(formatarMoeda(1234.5)).toMatch(/R\$\s1\.234,50/)
    expect(formatarMoeda(null)).toMatch(/R\$\s0,00/)
    expect(formatarData('2026-08-01')).toBe('01/08/2026')
    expect(formatarData(null)).toBe('—')
    expect(formatarDataHora('2026-08-01T15:00:00')).toBe('01/08/2026, 12:00')
    expect(formatarDataHora('inválida')).toBe('—')
  })
})
