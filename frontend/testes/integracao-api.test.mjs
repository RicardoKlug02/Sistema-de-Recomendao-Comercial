import { beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { solicitarApi, guardarSessao, obterSessao } from '../src/servicos/api.js'
import { entrar } from '../src/servicos/autenticacao.js'
import { importarArquivos, validarArquivo } from '../src/servicos/importacao.js'
import { adaptarAlerta, formatarMoeda } from '../src/servicos/dadosComerciais.js'

// Respostas controladas verificam o contrato sem criar usuários ou cargas no Render.
beforeEach(() => {
  const armazenamento = new Map()
  globalThis.sessionStorage = { getItem: (chave) => armazenamento.get(chave) ?? null, setItem: (chave, valor) => armazenamento.set(chave, valor), removeItem: (chave) => armazenamento.delete(chave) }
  globalThis.window = new EventTarget()
  globalThis.fetch = async () => { throw new Error('Requisição sem resposta configurada no teste.') }
})
const responder = (dados, status = 200) => new Response(JSON.stringify(dados), { status, headers: { 'Content-Type': 'application/json' } })

 test('login usa formulário OAuth2 e guarda a sessão sem a senha', async () => {
  globalThis.fetch = async (url, opcoes) => {
    assert.match(url, /\/api\/v1\/auth\/login$/)
    assert.equal(opcoes.body.get('username'), 'pessoa@exemplo.com')
    assert.equal(opcoes.body.get('password'), 'senha-teste')
    assert.equal(opcoes.headers.has('Authorization'), false)
    return responder({ access_token: 'token-teste', usuario_nome: 'Pessoa', usuario_email: 'pessoa@exemplo.com', usuario_perfil: 'admin' })
  }
  const resultado = await entrar({ email: ' pessoa@exemplo.com ', senha: 'senha-teste' })
  assert.equal(resultado.usuario.perfil, 'admin')
  assert.equal(obterSessao().token, 'token-teste')
  assert.equal(JSON.stringify(obterSessao()).includes('senha-teste'), false)
})

test('consultas protegidas enviam Bearer e expiração encerra a sessão', async () => {
  guardarSessao({ token: 'expirado', usuario: { email: 'pessoa@exemplo.com' } })
  let expirou = false
  window.addEventListener('sessao-expirada', () => { expirou = true })
  globalThis.fetch = async (_, opcoes) => {
    assert.equal(opcoes.headers.get('Authorization'), 'Bearer expirado')
    return responder({ detail: 'Token expirado' }, 401)
  }
  await assert.rejects(solicitarApi('/clientes/busca?termo=mercado'), /Token expirado/)
  assert.equal(obterSessao(), null)
  assert.equal(expirou, true)
})

test('erro de login mantém a mensagem do servidor e não cria sessão', async () => {
  globalThis.fetch = async () => responder({ detail: 'Cadastro pendente de aprovação.' }, 401)
  await assert.rejects(entrar({ email: 'pessoa@exemplo.com', senha: 'incorreta' }), /pendente de aprovação/)
  assert.equal(obterSessao(), null)
})

test('importação envia exatamente os dois campos multipart publicados', async () => {
  const pedidos = new File(['arquivo de teste'], 'pedidos.xls')
  const itens = new File(['arquivo de teste'], 'itens.xlsx')
  globalThis.fetch = async (url, opcoes) => {
    assert.match(url, /\/cargas\/excel$/)
    assert.equal(opcoes.method, 'POST')
    assert.deepEqual([...opcoes.body.keys()], ['arquivo_cabecalho', 'arquivo_itens'])
    assert.equal(opcoes.body.get('arquivo_cabecalho').name, 'pedidos.xls')
    assert.equal(opcoes.headers.has('Content-Type'), false)
    return responder({ status: 'sucesso', mensagem: 'Importação concluída: 3 pedidos.' })
  }
  assert.equal((await importarArquivos(pedidos, itens)).mensagem, 'Importação concluída: 3 pedidos.')
})

test('arquivo inválido é bloqueado antes do envio; erro do serviço não vira sucesso', async () => {
  const arquivo = new File(['teste'], 'valido.xlsx')
  assert.match(validarArquivo(new File([], 'vazio.xlsx')), /vazio/)
  await assert.rejects(importarArquivos(new File(['teste'], 'arquivo.txt'), arquivo), /XLS/)
  globalThis.fetch = async () => responder({ status: 'erro', mensagem: 'Planilhas incompatíveis' })
  await assert.rejects(importarArquivos(arquivo, arquivo), /incompatíveis/)
})

test('erros de validação e rede são apresentados ao usuário', async () => {
  globalThis.fetch = async () => responder({ detail: [{ msg: 'Campo obrigatório' }] }, 422)
  await assert.rejects(solicitarApi('/clientes/busca'), /Campo obrigatório/)
  globalThis.fetch = async () => { throw new TypeError('Failed to fetch') }
  await assert.rejects(solicitarApi('/clientes/busca'), /conectar ao servidor/)
})

test('timeout de upload alerta que a carga pode continuar no servidor', async () => {
  globalThis.fetch = async (_, opcoes) => new Promise((_, rejeitar) => opcoes.signal.addEventListener('abort', () => rejeitar(new DOMException('Cancelado', 'AbortError'))))
  await assert.rejects(solicitarApi('/cargas/excel', { method: 'POST', prazo: 5 }), /pode continuar processando/)
})

test('alertas preservam o cliente e diferenciam risco crítico de reposição', () => {
  const alerta = { cliente_id: 7, razao_social: 'Cliente real', produto_id: 3, nome_produto: 'Produto real', dias_atraso: 12, periodicidade_dias: 30, volume_medio_pedido: 8 }
  assert.equal(adaptarAlerta({ ...alerta, status: 'Risco Crítico de Churn' }, 0).prioridade, 'Alta')
  assert.equal(adaptarAlerta({ ...alerta, status: 'Atrasado' }, 0).tipo, 'Reposição')
  assert.equal(adaptarAlerta(alerta, 0).cliente.id, 7)
  assert.equal(formatarMoeda(null), 'Não disponível')
  assert.match(formatarMoeda(0), /0/)
})
