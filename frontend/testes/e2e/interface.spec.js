import { test, expect } from '@playwright/test'

const usuario = {
  nome: 'Equipe Exemplo',
  email: 'equipe@example.com',
  perfil: 'admin',
}
const cliente = {
  id: 1,
  razao_social: 'Comercial Exemplo',
  cidade: 'Indaial',
  estado: 'SC',
  grupo_economico: null,
}
const painel = {
  mes: '2026-08',
  indicadores: {
    venda_total: 125000,
    pedidos_emitidos: 80,
    clientes_atendidos: 25,
    ticket_medio: 1562.5,
    clientes_novos: 3,
    aberturas_cliente_fabrica: 5,
    clientes_reativados: 2,
    pedidos_sem_itens: 0,
  },
  faturamento_mensal: Array.from({ length: 12 }, (_, i) => ({
    mes: `2026-${String(i + 1).padStart(2, '0')}`,
    valor: 20000 + i * 9500,
  })),
  fabricas: [{ id: 1, nome: 'Fábrica Exemplo', valor: 65000 }],
  regioes: [{ nome: 'Blumenau', uf: 'SC', valor: 40000 }],
  clientes: [{ id: 1, nome: cliente.razao_social, valor: 12000 }],
  produtos: [{ id: 1, nome: 'Produto Exemplo', valor: 4500, quantidade: 90 }],
  aberturas: [
    {
      cliente_id: 1,
      cliente: cliente.razao_social,
      fabrica: 'Fábrica Exemplo',
      data: '01/08/2026',
      novo_no_escritorio: true,
    },
  ],
  fabricas_quentes: [{ nome: 'Fábrica Exemplo', crescimento: 12 }],
}

// Fixtures somente de teste. Rotas desconhecidas falham para revelar mudanças de contrato.
async function preparar(page, perfil = 'admin') {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const caminho = url.pathname.replace('/api/v1', '')
    let body
    if (caminho === '/auth/login')
      body = {
        access_token: 'token-de-teste',
        usuario_nome: usuario.nome,
        usuario_email: usuario.email,
        usuario_perfil: perfil,
      }
    else if (caminho === '/auth/me') body = { ...usuario, perfil }
    else if (caminho === '/comercial/vendedores')
      body = [{ id: 1, nome: 'Vendedor Exemplo' }]
    else if (caminho === '/comercial/fabricas')
      body = [{ id: 1, nome: 'Fábrica Exemplo' }]
    else if (caminho === '/comercial/historico-disponivel')
      body = { inicio: '2025-01-01', fim: '2026-10-18', pedidos: 80, ultima_importacao: null }
    else if (caminho === '/relatorios/redes')
      body = [{ nome: 'Rede Exemplo', clientes: 2 }]
    else if (caminho === '/relatorios/produtos-rede')
      body = { rede: 'Rede Exemplo', fabrica: 'Fábrica Exemplo', clientes: 2, total: 1, pedidos_sem_itens: 0,
        produtos: [{ produto_id: 1, sku: 'COD-EXEMPLO', nome: 'Produto Exemplo', fabrica: 'Fábrica Exemplo', ultima_compra: '2026-08-01', ultimo_preco: 12, pedido: '123', cliente: 'Filial Exemplo' }] }
    else if (caminho === '/relatorios/produtos-rede/pdf') {
      await route.fulfill({ contentType: 'application/pdf', body: '%PDF-1.4\n%%EOF' })
      return
    }
    else if (caminho === '/comercial/painel') body = painel
    else if (caminho === '/comercial/clientes')
      body = { total: 1, itens: [cliente] }
    else if (caminho === '/clientes/1')
      body = {
        ...cliente,
        clientes_agrupados: 1,
        valor_comprado: 12000,
        pedidos_emitidos: 8,
        ritmo_compras: null,
        comparacao_produtos: [],
        resumo_fabricas: [],
        sugestoes_reposicao: [],
        produtos_em_abandono: [],
        sugestoes_expansao_mix: [],
        sugestoes_fabricas: [],
      }
    else if (caminho === '/comercial/alertas')
      body = {
        total: 1,
        itens: [
          {
            id: 'a1',
            cliente_id: 1,
            cliente: cliente.razao_social,
            tipo: 'SEGUNDO_PEDIDO',
            descricao: 'Retome o contato para uma nova compra.',
            prioridade: 1,
          },
        ],
      }
    else if (caminho === '/auth/usuarios')
      body = [{ id: 1, ...usuario, aprovado: true }]
    else if (caminho === '/cargas/historico') body = []
    else
      return route.fulfill({
        status: 500,
        json: { detail: `Rota inesperada: ${caminho}` },
      })
    return route.fulfill({ json: body })
  })
}
async function entrar(page) {
  await page.goto('/')
  await page.getByLabel('E-mail', { exact: true }).fill(usuario.email)
  await page.getByLabel('Senha', { exact: true }).fill('senha-sintetica')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Visão geral', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('list', { name: 'Faturamento por mês' }),
  ).toBeVisible()
}

test('painel responsivo, filtros reais e sessão após recarregar', async ({
  page,
}, info) => {
  await preparar(page)
  await entrar(page)
  const logo = page.getByRole('img', {
    name: 'Rio Verde Representações',
    exact: true,
  })
  await expect(logo).toBeVisible()
  expect(await logo.evaluate((el) => el.naturalWidth)).toBeGreaterThan(0)
  const consulta = page.waitForRequest((r) => r.url().includes('vendedor_id=1'))
  await page.getByLabel('Vendedor', { exact: true }).selectOption('1')
  await consulta
  await expect(
    page.getByRole('list', { name: 'Faturamento por mês' }),
  ).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBeTruthy()
  await page.screenshot({
    path: `test-results/painel-${info.project.name}.png`,
    fullPage: true,
  })
  await page.reload()
  await expect(
    page.getByRole('heading', { name: 'Visão geral', exact: true }),
  ).toBeVisible()
})

test('cards de clientes, ficha, alertas e permissões de vendedor', async ({
  page,
}) => {
  await preparar(page, 'vendedor')
  await entrar(page)
  await expect(
    page.getByRole('link', { name: 'Usuários', exact: true }),
  ).toHaveCount(0)
  await expect(
    page.getByRole('link', { name: 'Importação', exact: true }),
  ).toHaveCount(0)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Abrir ficha', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: cliente.razao_social, exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Voltar para clientes' }).click()
  await expect(page.getByRole('button', { name: 'Abrir ficha' })).toBeVisible()
  await page.getByRole('link', { name: 'Alertas', exact: true }).click()
  await expect(page.getByText('Prioridade alta')).toBeVisible()
  await page.getByRole('button', { name: 'Consultar cliente' }).click()
  await expect(
    page.getByRole('heading', { name: cliente.razao_social, exact: true }),
  ).toBeVisible()
})

test('importação exige conferência e confirmação antes de gravar', async ({
  page,
}) => {
  await preparar(page)
  let gravacoes = 0
  await page.route('**/api/v1/cargas/conferir', (r) =>
    r.fulfill({
      json: {
        token_conferencia: 'conferencia-teste',
        inicio: '2026-08-01',
        fim: '2026-08-31',
        valor_total: 100,
        processados: 1,
        adicionados: 1,
        atualizados: 0,
        itens: 1,
        pedidos_sem_itens: 0,
        avisos: [],
        pedidos: [],
      },
    }),
  )
  await page.route('**/api/v1/cargas/excel', (r) => {
    gravacoes++
    return r.fulfill({
      json: {
        mensagem: 'Importação concluída.',
        processados: 1,
        adicionados: 1,
        atualizados: 0,
        itens: 1,
        pedidos_sem_itens: 0,
        avisos: [],
      },
    })
  })
  await entrar(page)
  await page.getByRole('link', { name: 'Importação', exact: true }).click()
  const arquivo = {
    name: 'teste.xlsx',
    mimeType:
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    buffer: Buffer.from('conteudo sintético interceptado'),
  }
  await page.getByLabel('1. Cabeçalhos dos pedidos').setInputFiles(arquivo)
  await page.getByLabel('2. Itens vendidos').setInputFiles(arquivo)
  await page.getByRole('button', { name: 'Conferir planilhas' }).click()
  await expect(
    page.getByRole('button', { name: 'Confirmar importação' }),
  ).toBeDisabled()
  expect(gravacoes).toBe(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy()
  await page.getByRole('checkbox').check()
  await expect(page.getByRole('checkbox')).toBeChecked()
  await page.getByRole('button', { name: 'Confirmar importação' }).click()
  await expect(page.getByRole('region', { name: 'Importar planilhas', exact: true }).getByRole('status')).toContainText(
    '1 pedidos: 1 novos e 0 atualizados; 1 itens importados.',
  )
  expect(gravacoes).toBe(1)
})

test('erro de API não aparece como faturamento zero', async ({ page }) => {
  await preparar(page)
  await page.route('**/api/v1/comercial/painel?*', (r) =>
    r.fulfill({
      status: 503,
      json: { detail: 'Serviço temporariamente indisponível.' },
    }),
  )
  await page.goto('/')
  await page.getByLabel('E-mail', { exact: true }).fill(usuario.email)
  await page.getByLabel('Senha', { exact: true }).fill('senha-sintetica')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText(
    'Serviço temporariamente indisponível.',
  )
  await expect(
    page.getByRole('heading', { name: 'Faturamento', exact: true }),
  ).toHaveCount(0)
})

test('sincronização mensal confere exclusões e invalida confirmação ao trocar o mês', async ({ page }) => {
  await preparar(page)
  let gravacoes = 0
  let ultimaCarga = ''
  await page.route('**/api/v1/cargas/conferir', (r) => r.fulfill({ json: {
    token_conferencia: 'token-mes', modo: 'sincronizar_mes', mes: '2026-08',
    inicio: '2026-08-01', fim: '2026-08-31', valor_total: 20, valor_excluido: 200,
    processados: 1, adicionados: 0, atualizados: 1, itens: 1, pedidos_sem_itens: 0,
    excluidos: 1, itens_removidos: 2, quantidades_reduzidas: 1, avisos: [], pedidos: [],
    pedidos_excluidos: [{ pedido: '999', fabrica: 'Fábrica Exemplo', data: '2026-08-15', valor: 200, itens: 1 }],
  } }))
  await page.route('**/api/v1/cargas/excel', (r) => {
    gravacoes++
    ultimaCarga = r.request().postData()
    return r.fulfill({ json: { modo: 'sincronizar_mes', mes: '2026-08', processados: 1, adicionados: 0,
      atualizados: 1, itens: 1, excluidos: 1, itens_removidos: 2, quantidades_reduzidas: 1, avisos: [] } })
  })
  await entrar(page)
  await page.getByRole('link', { name: 'Importação', exact: true }).click()
  await page.getByLabel('Modo de importação').selectOption('sincronizar_mes')
  await page.getByLabel('Mês a sincronizar').fill('2026-08')
  const arquivo = { name: 'mes.xlsx', mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer: Buffer.from('teste interceptado') }
  await page.getByLabel('1. Cabeçalhos dos pedidos').setInputFiles(arquivo)
  await page.getByLabel('2. Itens vendidos').setInputFiles(arquivo)
  await page.getByRole('button', { name: 'Conferir planilhas' }).click()
  await expect(page.getByRole('heading', { name: 'Pedidos que serão excluídos' })).toBeVisible()
  await expect(page.getByRole('cell', { name: '999', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Confirmar importação' })).toBeDisabled()
  expect(gravacoes).toBe(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy()
  await page.getByRole('checkbox').check()
  await page.getByLabel('Mês a sincronizar').fill('2026-07')
  await expect(page.getByRole('heading', { name: 'Confira antes de importar' })).toHaveCount(0)
  await page.getByLabel('Mês a sincronizar').fill('2026-08')
  await page.getByRole('button', { name: 'Conferir planilhas' }).click()
  await expect(page.getByRole('checkbox')).not.toBeChecked()
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Confirmar importação' }).click()
  await expect(page.getByRole('region', { name: 'Importar planilhas', exact: true }).getByRole('status')).toContainText('1 pedidos excluídos')
  expect(gravacoes).toBe(1)
  expect(ultimaCarga).toContain('sincronizar_mes')
  expect(ultimaCarga).toContain('2026-08')
  expect(ultimaCarga).toContain('confirmar_sincronizacao')
})

test('relatório da rede filtra fábrica e baixa PDF autenticado', async ({ page }) => {
  await preparar(page)
  await entrar(page)
  await page.getByRole('link', { name: 'Relatórios', exact: true }).click()
  await page.getByLabel('Rede de clientes', { exact: true }).selectOption('Rede Exemplo')
  const pedido = page.waitForRequest(r => r.url().includes('/relatorios/produtos-rede?') && r.url().includes('fabrica_id=1'))
  await page.getByLabel('Fábrica', { exact: true }).selectOption('1')
  await pedido
  await expect(page.getByRole('cell', { name: 'COD-EXEMPLO', exact: true })).toBeVisible()
  const pdf = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Baixar PDF', exact: true }).click()
  expect((await pdf).suggestedFilename()).toBe('produtos-da-rede.pdf')
})

test('alertas preservam fábrica e vendedor ao voltar e registram acompanhamento', async ({ page }) => {
  await preparar(page)
  let versao = 0
  let motivo = ''
  let situacao = 'PENDENTE'
  const assinatura = 'a'.repeat(64)
  await page.route('**/api/v1/comercial/alertas?*', (route) => route.fulfill({ json: {
    total: 1, total_alertas: 1, itens: [{ id: 'cliente:1', cliente_id: 1, cliente: cliente.razao_social,
      prioridade: 1, assinatura, resumo: { FABRICA_INATIVA: 1 },
      alertas: [{ id: 'f1', tipo: 'FABRICA_INATIVA', descricao: 'Fábrica Exemplo: inativa.' }],
      acompanhamento: { versao, situacao, motivo, proximo_contato: null, atualizado_em: '2026-10-18T12:00:00Z', usuario: versao ? usuario.nome : null },
    }],
  } }))
  await page.route('**/api/v1/comercial/alertas/1/acompanhamento', async (route) => {
    const entrada = route.request().postDataJSON()
    expect(entrada.assinatura).toBe(assinatura)
    expect(entrada.versao).toBe(versao)
    versao++; motivo = entrada.motivo; situacao = entrada.situacao
    return route.fulfill({ json: { versao, situacao } })
  })
  await page.route('**/api/v1/comercial/alertas/1/historico', (route) => route.fulfill({ json: [
    { versao, situacao, motivo, usuario: usuario.nome, atualizado_em: '2026-10-18T12:00:00Z', proximo_contato: null },
  ] }))
  await entrar(page)
  await page.getByRole('link', { name: 'Alertas', exact: true }).click()
  await page.getByLabel('Vendedor', { exact: true }).selectOption('1')
  await page.getByLabel('Fábrica', { exact: true }).selectOption('1')
  await expect(page.getByText('1 × Fábrica inativa', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Consultar cliente' }).click()
  await expect(page.getByRole('heading', { name: cliente.razao_social, exact: true })).toBeVisible()
  await expect(page.getByLabel('Fábrica', { exact: true })).toHaveValue('1')
  await page.getByRole('button', { name: 'Voltar aos alertas' }).click()
  await expect(page.getByLabel('Vendedor', { exact: true })).toHaveValue('1')
  await expect(page.getByLabel('Fábrica', { exact: true })).toHaveValue('1')
  await page.getByText('Registrar acompanhamento', { exact: true }).click()
  await page.getByLabel('Situação do acompanhamento').selectOption('CONTATADO')
  await page.getByLabel('Motivo ou observação').fill('Contato de demonstração')
  await page.getByRole('button', { name: 'Salvar acompanhamento' }).click()
  await expect(page.getByText('Acompanhamento: Contatado', { exact: true })).toBeVisible()
  await page.getByText('Histórico de acompanhamento', { exact: true }).click()
  await expect(page.locator('ol').getByText('Contato de demonstração', { exact: true })).toBeVisible()
})

test('consulta com erro pode ser tentada novamente sem recarregar', async ({ page }) => {
  await preparar(page)
  let falhar = true
  await page.route('**/api/v1/comercial/clientes?*', (route) => falhar
    ? route.fulfill({ status: 503, json: { detail: 'Falha temporária de demonstração.' } })
    : route.fulfill({ json: { total: 1, itens: [cliente] } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await expect(page.getByText('Falha temporária de demonstração.', { exact: true })).toBeVisible()
  falhar = false
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Abrir ficha', exact: true })).toBeVisible()
})

test('ficha distingue fábricas com mesmo código e separa ciclo de inatividade', async ({ page }) => {
  await preparar(page)
  await page.route('**/api/v1/clientes/1?*', (route) => route.fulfill({ json: {
    ...cliente, cliente_id: 1, clientes_agrupados: 1, cadastros_fiscais: [], valor_comprado: 100,
    pedidos_emitidos: 3, ritmo_compras: null, comparacao_produtos: [], produtos_em_abandono: [],
    produtos_sem_confirmacao: [], sugestoes_expansao_mix: [], sugestoes_fabricas: [],
    resumo_fabricas: [{ fabrica_id: 1, fabrica: 'Fábrica Exemplo', ultima_compra: '01/10/2026',
      data_limite_inatividade: '30/12/2026', situacao_atividade: 'Ativa', situacao_recompra: 'Recompra atrasada há 7 dias' }],
    sugestoes_reposicao: [
      { produto_id: 1, fabrica: 'Fábrica Exemplo', sku: '21053', nome: 'Produto A', status: 'Janela Ideal', volume_habitual: 10 },
      { produto_id: 2, fabrica: 'Outra fábrica', sku: '21053', nome: 'Produto B', status: 'Janela Ideal', volume_habitual: 5 },
    ],
  } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Abrir ficha', exact: true }).click()
  await expect(page.getByText('Fábrica Exemplo · Código 21053', { exact: true })).toBeVisible()
  await expect(page.getByText('Outra fábrica · Código 21053', { exact: true })).toBeVisible()
  await expect(page.getByText('Ativa', { exact: true })).toBeVisible()
  await expect(page.getByText('Recompra atrasada há 7 dias', { exact: true })).toBeVisible()
})

test('ficha mostra mais produtos aos poucos e busca por código ou nome', async ({ page }) => {
  await preparar(page)
  const reposicao = Array.from({ length: 12 }, (_, i) => ({ produto_id: i + 1, fabrica: 'Fábrica Exemplo',
    sku: String(3000 + i), nome: i === 11 ? 'Sabão em pó' : `Produto ${i + 1}`, status: 'Janela Ideal', volume_habitual: 4 }))
  await page.route('**/api/v1/clientes/1?*', (route) => route.fulfill({ json: {
    ...cliente, cliente_id: 1, clientes_agrupados: 1, cadastros_fiscais: [], valor_comprado: 100,
    pedidos_emitidos: 3, ritmo_compras: null, comparacao_produtos: [], produtos_em_abandono: [],
    produtos_sem_confirmacao: [], sugestoes_expansao_mix: [], sugestoes_fabricas: [], resumo_fabricas: [],
    sugestoes_reposicao: reposicao,
  } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Abrir ficha', exact: true }).click()
  const cartao = page.getByRole('region', { name: 'Reposição de produtos' })
  await expect(cartao.getByRole('listitem')).toHaveCount(5)
  await cartao.getByRole('button', { name: 'Mostrar mais (7)' }).click()
  await expect(cartao.getByRole('listitem')).toHaveCount(12)
  await expect(cartao.getByRole('button', { name: /Mostrar mais/ })).toHaveCount(0)
  await cartao.getByRole('button', { name: 'Mostrar menos' }).click()
  await expect(cartao.getByRole('listitem')).toHaveCount(5)
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('sabao')
  await expect(cartao.getByRole('listitem')).toHaveCount(1)
  await expect(cartao.getByText('Fábrica Exemplo · Código 3011')).toBeVisible()
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('3003')
  await expect(cartao.getByRole('listitem')).toHaveCount(1)
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('inexistente')
  await expect(cartao.getByText('Nenhum produto encontrado para “inexistente”.')).toBeVisible()
})

test('comparação de produtos combina busca, fábrica e variação com mostrar mais', async ({ page }, testInfo) => {
  await preparar(page)
  const comparacao = Array.from({ length: 25 }, (_, i) => ({ produto_id: i + 1, sku: String(3000 + i),
    nome: i === 24 ? 'Sabão em pó' : `Produto ${i + 1}`, fabrica: i % 2 ? 'Mec Tronic' : 'Fábrica Águia',
    media_habitual: 10, recente: 5, variacao_pct: i >= 20 ? null : i % 3 === 0 ? -25 : i % 3 === 1 ? 50 : 0,
    status: i >= 20 ? ['ITENS_INCOMPLETOS', 'HISTORICO_INSUFICIENTE', 'SEM_BASE_COMPARACAO'][i % 3] : 'COMPARAVEL',
  }))
  const metrica = { media_habitual: 100, recente: 80, variacao_pct: -20, status: 'COMPARAVEL' }
  await page.route('**/api/v1/clientes/1?*', (r) => r.fulfill({ json: {
    ...cliente, clientes_agrupados: 1, valor_comprado: 100, pedidos_emitidos: 3, cadastros_fiscais: [],
    ritmo_compras: { inicio_recente: '2026-09-29', fim_recente: '2026-10-28', inicio_habitual: '2026-07-01',
      fim_habitual: '2026-09-28', historico_suficiente: true, valor: metrica, pedidos: metrica },
    comparacao_produtos: comparacao, resumo_fabricas: [], sugestoes_reposicao: [],
    produtos_em_abandono: [], produtos_sem_confirmacao: [], sugestoes_expansao_mix: [], sugestoes_fabricas: [],
  } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Abrir ficha', exact: true }).click()
  const cartao = page.getByRole('region', { name: 'Ritmo de compras', exact: true })
  const tabela = cartao.getByRole('table', { name: 'Comparação de quantidades por produto' })
  await expect(tabela.locator('tbody tr')).toHaveCount(10)
  await cartao.getByRole('button', { name: 'Mostrar mais (15)' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(20)
  await cartao.getByRole('button', { name: 'Mostrar mais (5)' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(25)
  await cartao.getByRole('button', { name: 'Mostrar menos' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(10)
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('3024 sabao aguia')
  await expect(tabela.locator('tbody tr')).toHaveCount(1)
  await expect(tabela).toContainText('Código 3024')
  await cartao.getByRole('button', { name: 'Limpar filtros' }).click()
  await cartao.getByLabel('Fábrica dos produtos').selectOption('Mec Tronic')
  await expect(tabela.locator('tbody tr')).toHaveCount(10)
  await cartao.getByRole('button', { name: 'Mostrar mais (2)' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(12)
  await cartao.getByLabel('Variação nas compras').selectOption('queda')
  await expect(tabela.locator('tbody tr')).toHaveCount(3)
  await cartao.getByLabel('Variação nas compras').selectOption('aumento')
  await expect(tabela.locator('tbody tr')).toHaveCount(4)
  await cartao.getByLabel('Variação nas compras').selectOption('estavel')
  await expect(tabela.locator('tbody tr')).toHaveCount(3)
  await cartao.getByLabel('Variação nas compras').selectOption('sem_comparacao')
  await expect(tabela.locator('tbody tr')).toHaveCount(2)
  await expect(cartao.getByRole('row', { name: /Valor comprado/ })).toContainText('80,00')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy()
  await cartao.screenshot({ path: `../output/usabilidade/comparacao-filtrada-${testInfo.project.name}.png` })
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('inexistente')
  await expect(tabela).toHaveCount(0)
  await expect(cartao.getByText('Mostrando 0 de 0 produtos (25 no total).')).toBeVisible()
  await cartao.getByRole('button', { name: 'Limpar filtros' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(10)
  await expect(cartao.getByLabel('Fábrica dos produtos')).toHaveValue('')
  await expect(cartao.getByLabel('Variação nas compras')).toHaveValue('')
})

test('listas de abandono e recompra não confirmada possuem filtros independentes', async ({ page }, testInfo) => {
  await preparar(page)
  const lista = Array.from({ length: 12 }, (_, i) => ({ produto_id: i + 1, sku: String(4000 + i),
    nome: `Produto ${i + 1}`, fabrica: i % 2 ? 'Mec Tronic' : 'Fábrica Águia', dias_parado: 120 }))
  await page.route('**/api/v1/clientes/1?*', (r) => r.fulfill({ json: {
    ...cliente, clientes_agrupados: 1, valor_comprado: 100, pedidos_emitidos: 3, cadastros_fiscais: [], ritmo_compras: null,
    comparacao_produtos: [], resumo_fabricas: [], sugestoes_reposicao: [], sugestoes_expansao_mix: [], sugestoes_fabricas: [],
    produtos_em_abandono: lista, produtos_sem_confirmacao: lista.slice(0, 8),
  } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Abrir ficha', exact: true }).click()
  const confirmado = page.getByRole('region', { name: 'Produtos com abandono confirmado', exact: true })
  const incerto = page.getByRole('region', { name: 'Produtos com recompra não confirmada', exact: true })
  await expect(confirmado.getByRole('listitem')).toHaveCount(5)
  await expect(incerto.getByRole('listitem')).toHaveCount(5)
  await confirmado.getByRole('button', { name: 'Mostrar mais (7)' }).click()
  await expect(confirmado.getByRole('listitem')).toHaveCount(12)
  await confirmado.getByLabel('Fábrica dos produtos').selectOption('Mec Tronic')
  await expect(confirmado.getByRole('listitem')).toHaveCount(5)
  await confirmado.getByRole('button', { name: 'Mostrar mais (1)' }).click()
  await expect(confirmado.getByRole('listitem')).toHaveCount(6)
  await confirmado.getByLabel('Buscar por código, nome ou fábrica').fill('4011')
  await expect(confirmado.getByRole('listitem')).toHaveCount(1)
  await expect(incerto.getByRole('listitem')).toHaveCount(5)
  await incerto.getByRole('button', { name: 'Mostrar mais (3)' }).click()
  await expect(incerto.getByRole('listitem')).toHaveCount(8)
  await confirmado.getByRole('button', { name: 'Limpar filtros' }).click()
  await expect(confirmado.getByRole('listitem')).toHaveCount(5)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy()
  await page.getByRole('region', { name: 'Produtos em abandono', exact: true }).screenshot({ path: `../output/usabilidade/abandono-filtrado-${testInfo.project.name}.png` })
})

test('relatório de códigos limita a lista e mantém o PDF completo após a busca', async ({ page }) => {
  await preparar(page)
  const produtos = Array.from({ length: 45 }, (_, i) => ({ produto_id: i + 1, sku: String(5000 + i),
    nome: `Produto ${i + 1}`, fabrica: 'Fábrica Exemplo', ultima_compra: '2026-08-01',
    ultimo_preco: 12, pedido: String(i + 1), cliente: 'Filial Exemplo' }))
  await page.route('**/api/v1/relatorios/produtos-rede?*', (r) => r.fulfill({ json: {
    rede: 'Rede Exemplo', fabrica: 'Fábrica Exemplo', clientes: 2, total: 45, pedidos_sem_itens: 0, produtos,
  } }))
  await entrar(page)
  await page.getByRole('link', { name: 'Relatórios', exact: true }).click()
  await page.getByLabel('Rede de clientes').selectOption('Rede Exemplo')
  const cartao = page.getByRole('region', { name: 'Códigos comprados pela rede', exact: true })
  const tabela = cartao.getByRole('table', { name: 'Códigos comprados pela rede' })
  await expect(tabela.locator('tbody tr')).toHaveCount(20)
  await cartao.getByRole('button', { name: 'Mostrar mais (25)' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(40)
  await cartao.getByRole('button', { name: 'Mostrar mais (5)' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(45)
  await cartao.getByRole('button', { name: 'Mostrar menos' }).click()
  await expect(tabela.locator('tbody tr')).toHaveCount(20)
  await cartao.getByLabel('Buscar por código, nome ou fábrica').fill('5044')
  await expect(tabela.locator('tbody tr')).toHaveCount(1)
  const pedidoPdf = page.waitForRequest((r) => r.url().includes('/relatorios/produtos-rede/pdf'))
  const download = page.waitForEvent('download')
  await cartao.getByRole('button', { name: 'Baixar PDF', exact: true }).click()
  const urlPdf = new URL((await pedidoPdf).url())
  expect(urlPdf.searchParams.get('rede')).toBe('Rede Exemplo')
  expect(urlPdf.searchParams.has('termo')).toBe(false)
  expect((await download).suggestedFilename()).toBe('produtos-da-rede.pdf')
})
