import { useRef, useState } from 'react'
import FormField from './FormField'
import { login, requestPasswordReset, validateEmail } from '../services/auth'

export default function AuthForm({ mode, onSuccess, onNavigate }) {
  const isLogin = mode === 'login'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [requestError, setRequestError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const pending = useRef(false)

  async function handleSubmit(event) {
    event.preventDefault()
    if (pending.current || isComplete) return
    const nextErrors = {
      email: validateEmail(email),
      password: isLogin && !password.trim() ? 'Informe sua senha.' : '',
    }
    setErrors(nextErrors)
    setRequestError('')
    const firstInvalid = Object.keys(nextErrors).find((key) => nextErrors[key])
    if (firstInvalid) {
      event.currentTarget.elements.namedItem(firstInvalid).focus()
      return
    }
    pending.current = true
    setIsSubmitting(true)
    try {
      if (isLogin) {
        const result = await login({ email, password })
        setPassword('')
        onSuccess(result.user)
      } else {
        await requestPasswordReset({ email })
        setIsComplete(true)
      }
    } catch {
      setRequestError(isLogin
        ? 'Não foi possível entrar. Tente novamente.'
        : 'Não foi possível solicitar a recuperação. Tente novamente.')
    } finally {
      pending.current = false
      setIsSubmitting(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate aria-busy={isSubmitting}>
      {isComplete ? (
        <p className="feedback-message" role="status">
          Solicitação simulada para <strong>{email.trim()}</strong>.
        </p>
      ) : (
        <>
          <FormField id="email" label="Email" type="email" autoComplete={isLogin ? 'username' : 'email'}
            placeholder="usuario@rioverdeindaial.com.br" value={email} error={errors.email}
            disabled={isSubmitting} onChange={(event) => {
              setEmail(event.target.value)
              setErrors((current) => ({ ...current, email: '' }))
            }} />
          {isLogin && <FormField id="password" label="Senha" type="password" autoComplete="current-password"
            placeholder="Digite sua senha aqui" value={password} error={errors.password}
            disabled={isSubmitting} onChange={(event) => {
              setPassword(event.target.value)
              setErrors((current) => ({ ...current, password: '' }))
            }} />}
          {requestError && <p className="field-error" role="alert">{requestError}</p>}
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? (isLogin ? 'Entrando…' : 'Solicitando…') : (isLogin ? 'Entrar' : 'Recuperar senha')}
          </button>
          <span className="sr-only" role="status">{isSubmitting ? 'Aguarde, processando solicitação.' : ''}</span>
        </>
      )}
      <button className="text-button" type="button" disabled={isSubmitting} onClick={onNavigate}>
        {isLogin ? 'Esqueceu a senha?' : 'Voltar para o login'}
      </button>
    </form>
  )
}
