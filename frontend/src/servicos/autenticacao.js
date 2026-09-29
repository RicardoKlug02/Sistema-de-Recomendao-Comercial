import { guardarSessao, solicitarApi } from './api.js'

export function validarEmail(email) {
  if (!email.trim()) return 'Informe seu e-mail.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Informe um e-mail válido.'
  return ''
}

export async function entrar({ email, senha }) {
  if (validarEmail(email) || !senha) throw new Error('Confira o e-mail e a senha informados.')
  const dados = await solicitarApi('/auth/login', {
    publico: true,
    method: 'POST',
    body: new URLSearchParams({ username: email.trim(), password: senha }),
  })
  if (!dados.access_token || !dados.usuario_email)
    throw new Error('O servidor não retornou uma sessão válida.')
  const usuario = { nome: dados.usuario_nome, email: dados.usuario_email, perfil: dados.usuario_perfil }
  guardarSessao({ token: dados.access_token, usuario })
  return { usuario }
}
