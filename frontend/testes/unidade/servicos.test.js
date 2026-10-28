import { beforeEach, describe, expect, test, vi } from 'vitest'
import { obterSessao } from '../../src/servicos/api'
import { ehGestor, entrar, registrar, validarEmail } from '../../src/servicos/autenticacao'
import { correspondeVariacao, filtrarProdutos } from '../../src/servicos/busca'
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

  test('sincronização mensal vincula mês e confirmação às duas etapas', async () => {
    fetch.mockResolvedValue(responder({ mensagem: 'Conferido.' }))
    const escopo = { modo: 'sincronizar_mes', mes: '2026-08' }
    await importarArquivos(planilha('pedidos.xlsx'), planilha('itens.xlsx'), undefined, escopo)
    const previa = fetch.mock.calls[0][1].body
    expect(previa.get('modo')).toBe('sincronizar_mes')
    expect(previa.get('mes')).toBe('2026-08')
    expect(previa.has('confirmar_sincronizacao')).toBe(false)
    await importarArquivos(planilha('pedidos.xlsx'), planilha('itens.xlsx'), 'token', escopo)
    expect(fetch.mock.calls[1][1].body.get('confirmar_sincronizacao')).toBe('true')
  })

  test('sincronização sem mês não envia arquivos', async () => {
    await expect(importarArquivos(planilha('pedidos.xlsx'), planilha('itens.xlsx'), undefined,
      { modo: 'sincronizar_mes' })).rejects.toThrow('Selecione o mês')
    expect(fetch).not.toHaveBeenCalled()
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

describe('busca de produtos', () => {
  const produtos = [
    { produto_id: 1, sku: '1020', nome: 'Detergente Limão' },
    { produto_id: 2, sku: 'AB-77', nome: 'Sabão em pó' },
  ]
  test('encontra por código ou nome, sem diferenciar acento e maiúscula', () => {
    expect(filtrarProdutos(produtos, '102')).toEqual([produtos[0]])
    expect(filtrarProdutos(produtos, 'ab-77')).toEqual([produtos[1]])
    expect(filtrarProdutos(produtos, 'SABAO')).toEqual([produtos[1]])
    expect(filtrarProdutos(produtos, 'limao')).toEqual([produtos[0]])
  })
  test('termo vazio devolve a lista inteira', () => {
    expect(filtrarProdutos(produtos, '  ')).toBe(produtos)
    expect(filtrarProdutos(produtos, 'inexistente')).toEqual([])
  })
  test('combina palavras do código, nome e fábrica sem depender da ordem', () => {
    const lista = [{ ...produtos[0], fabrica: 'Fábrica Águia' }, { ...produtos[1], fabrica: 'Mec Tronic' }]
    expect(filtrarProdutos(lista, 'aguia limao 1020')).toEqual([lista[0]])
    expect(filtrarProdutos(lista, '  tronic   SABAO ')).toEqual([lista[1]])
    expect(filtrarProdutos(lista, 'aguia sabao')).toEqual([])
    expect(filtrarProdutos(lista, 'mec')).toEqual([lista[1]])
  })
})

describe('filtros da comparação de produtos', () => {
  test('distingue queda, aumento e estabilidade sem criar um limite de atenção', () => {
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: -0.1 }, 'queda')).toBe(true)
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: 0.1 }, 'aumento')).toBe(true)
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: 0 }, 'estavel')).toBe(true)
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: 0 }, 'queda')).toBe(false)
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: -10 }, 'aumento')).toBe(false)
  })
  test('ausência de comparação não aparece como queda nem como estabilidade', () => {
    for (const status of ['HISTORICO_INSUFICIENTE', 'SEM_BASE_COMPARACAO', 'ITENS_INCOMPLETOS']) {
      const produto = { status, variacao_pct: null }
      expect(correspondeVariacao(produto, 'sem_comparacao')).toBe(true)
      expect(correspondeVariacao(produto, 'queda')).toBe(false)
      expect(correspondeVariacao(produto, 'estavel')).toBe(false)
      expect(correspondeVariacao(produto, '')).toBe(true)
    }
    expect(correspondeVariacao({ status: 'COMPARAVEL', variacao_pct: Number.NaN }, 'sem_comparacao')).toBe(true)
  })
})
