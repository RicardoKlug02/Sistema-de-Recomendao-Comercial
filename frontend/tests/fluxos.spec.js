import { test, expect } from "@playwright/test";
async function entrar(page, email = "admin@example.com") {
  await page.goto("/#/entrar");
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill("TesteSeguro123");
  await page.getByRole("button", { name: "Entrar na plataforma" }).click();
  await expect(
    page.getByRole("heading", { name: "Visão geral", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Carregando informações…")).toHaveCount(0);
}
test("cliente específico, histórico, recomendações e navegação", async ({
  page,
}, info) => {
  await entrar(page);
  await page.getByRole("link", { name: "Clientes", exact: true }).click();
  await page.getByRole("link", { name: "Abrir ficha" }).click();
  await expect(page).toHaveURL(/clientes\/1/);
  await expect(
    page.getByRole("heading", { name: "Comercial Exemplo" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Histórico de compras" }).click();
  await expect(page.getByText("TESTE-3", { exact: true })).toBeVisible();
  await page.locator("summary").first().click();
  await expect(
    page.getByText("Cabo elétrico de teste · 10 × R$").first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Recomendações", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Expansão de mix" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Visão geral", exact: true }).click();
  await page.screenshot({
    path: `test-results/ficha-${info.project.name}.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("link", { name: "Voltar para clientes" }).click();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Comercial Exemplo" }),
  ).toBeVisible();
});
test("telas comerciais, filtros e importação", async ({ page }) => {
  await entrar(page);
  await page.getByRole("link", { name: "Oportunidades", exact: true }).click();
  await page.getByRole("checkbox").first().check();
  await page.getByRole("button", { name: "Buscar sugestões" }).click();
  await expect(page.getByText("Não há evidências suficientes")).toBeVisible();
  await page.getByRole("link", { name: "Alertas", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Acompanhamento de recompra" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Relatórios", exact: true }).click();
  await page.getByLabel("Cliente", { exact: true }).fill("inexistente");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page.getByText("Nenhum registro encontrado.")).toBeVisible();
  await page.getByRole("link", { name: "Importação", exact: true }).click();
  await expect(page.getByText("1. Pedidos / cabeçalho")).toBeVisible();
  await expect(page.getByText("2. Produtos vendidos / itens")).toBeVisible();
  await page.getByRole("link", { name: "Usuários", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "Admin de Teste", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Minha conta", exact: true }).click();
  await expect(page.getByLabel("Senha atual")).toBeVisible();
});
test("cadastro, recuperação, reset inválido e login inválido", async ({
  page,
}) => {
  await page.goto("/#/cadastro");
  await page.getByLabel("Nome completo").fill("Usuário de Teste");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill(`novo-${Date.now()}@example.com`);
  await page.getByLabel("Senha", { exact: true }).fill("TesteSeguro123");
  await page.getByRole("button", { name: "Solicitar cadastro" }).click();
  await expect(page.getByText("Cadastro realizado.")).toBeVisible();
  await page.goto("/#/recuperar");
  await page.getByLabel("E-mail", { exact: true }).fill("admin@example.com");
  await page.getByRole("button", { name: "Enviar link" }).click();
  await expect(page.getByRole("alert")).toContainText("indisponível");
  await page.goto("/#/redefinir?token=invalido");
  await page.getByLabel("Nova senha", { exact: true }).fill("TesteSeguro123");
  await page.getByLabel("Confirmar senha").fill("TesteSeguro123");
  await page.getByRole("button", { name: "Salvar senha" }).click();
  await expect(page.getByRole("alert")).toContainText("inválido");
});
test("vendedor não acessa administração e mantém link do cliente no login", async ({
  page,
}) => {
  await entrar(page, "vendedor@example.com");
  await expect(
    page.getByRole("link", { name: "Usuários", exact: true }),
  ).toHaveCount(0);
  await page.goto("/#/usuarios");
  await expect(page.getByRole("alert")).toContainText("restrito");
  await page.goto("/#/clientes/1");
  await page.reload();
  await page.getByLabel("E-mail", { exact: true }).fill("vendedor@example.com");
  await page.getByLabel("Senha", { exact: true }).fill("TesteSeguro123");
  await page.getByRole("button", { name: "Entrar na plataforma" }).click();
  await expect(
    page.getByRole("heading", { name: "Comercial Exemplo" }),
  ).toBeVisible();
});
