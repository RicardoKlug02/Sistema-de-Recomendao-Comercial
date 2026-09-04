import { useEffect, useRef, useState } from 'react'
import AuthCard from './components/AuthCard'
import AuthForm from './components/AuthForm'
import './App.css'

export default function App() {
  const [screen, setScreen] = useState('login')
  const [user, setUser] = useState(null)
  const headingRef = useRef(null)
  useEffect(() => { headingRef.current?.focus() }, [screen])
  const titles = {
    login: ['Sistema de Recomendação Rio Verde Rep', 'Acesse sua conta para continuar'],
    recovery: ['Recuperar senha', 'Informe o e-mail da sua conta'],
    success: ['Deu certo', 'Seu acesso foi simulado com sucesso'],
  }
  const [title, subtitle] = titles[screen]
  return (
    <main className="auth-page">
      <AuthCard title={title} subtitle={subtitle} headingRef={headingRef}>
        {screen === 'success' ? (
          <section className="auth-form success-panel" aria-label="Acesso simulado">
            <p className="account-email">{user.email}</p>
            <p>Falta autenticar e conectar</p>
            <button className="primary-button" onClick={() => {
              setUser(null)
              setScreen('login')
            }}>Sair</button>
          </section>
        ) : (
          <AuthForm key={screen} mode={screen}
            onNavigate={() => setScreen(screen === 'login' ? 'recovery' : 'login')}
            onSuccess={(account) => { setUser(account); setScreen('success') }} />
        )}
      </AuthCard>
    </main>
  )
}
