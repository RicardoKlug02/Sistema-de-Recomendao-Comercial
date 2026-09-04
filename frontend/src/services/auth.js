// Teste de funcionamento, depois tenho que fazer a call para backend
const simularRequest = () => new Promise((resolve) => setTimeout(resolve, 600))

export function validateEmail(email) {
  if (!email.trim()) return 'Informe seu e-mail.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Informe um e-mail válido.'
  return ''
}

export async function login({ email, password }) {
  if (validateEmail(email) || !password.trim()) throw new Error('Confira o e-mail e a senha informados.')
  // POST depois autenticar
  await simularRequest()
  return { user: { email: email.trim() } }
}

export async function requestPasswordReset({ email }) {
  if (validateEmail(email)) throw new Error('Informe um e-mail válido.')
  // POST email para recuperar senha
  await simularRequest()
}
