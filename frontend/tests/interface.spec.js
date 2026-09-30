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
      () => document.documentElement.scrollWidth <= innerWidth,
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
  await page.getByRole('checkbox').check()
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
