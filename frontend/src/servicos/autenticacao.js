import { solicitar, salvarSessao } from './api'

export function validarEmail(email) {
  if (!email.trim()) return 'Informe seu e-mail.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Informe um e-mail válido.'
  return ''
}
export async function entrar({ email, senha }) {
  const dados = await solicitar('/auth/login', { method: 'POST',
    body: new URLSearchParams({ username: email.trim(), password: senha }) })
  const usuario = { nome: dados.usuario_nome, email: dados.usuario_email, perfil: dados.usuario_perfil }
  salvarSessao({ access_token: dados.access_token, usuario })
  return { usuario }
}
export async function registrar({ nome, email, senha }) {
  return solicitar('/auth/registrar', { method: 'POST', body: { nome, email, senha } })
}
