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
  await cartao.getByLabel('Buscar por código ou nome').fill('sabao')
  await expect(cartao.getByRole('listitem')).toHaveCount(1)
  await expect(cartao.getByText('Fábrica Exemplo · Código 3011')).toBeVisible()
  await cartao.getByLabel('Buscar por código ou nome').fill('3003')
  await expect(cartao.getByRole('listitem')).toHaveCount(1)
  await cartao.getByLabel('Buscar por código ou nome').fill('inexistente')
  await expect(cartao.getByText('Nenhum produto encontrado para “inexistente”.')).toBeVisible()
})
