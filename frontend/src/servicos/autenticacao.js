// Simula autenticação até a integração com o servidor.
const simularSolicitacao = () => new Promise((resolver) => setTimeout(resolver, 600))

export function validarEmail(email) {
  if (!email.trim()) return 'Informe seu e-mail.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Informe um e-mail válido.'
  return ''
}

export async function entrar({ email, senha }) {
  if (validarEmail(email) || !senha.trim()) throw new Error('Confira o e-mail e a senha informados.')
  await simularSolicitacao()
  return { usuario: { email: email.trim() } }
}

export async function solicitarRecuperacaoSenha({ email }) {
  if (validarEmail(email)) throw new Error('Informe um e-mail válido.')
  await simularSolicitacao()
}
