export default function AuthCard({ title, subtitle, headingRef, children }) {
  return (
    <section className="auth-card" aria-labelledby="auth-title">
      <header className="auth-header">
        <h1 id="auth-title" ref={headingRef} tabIndex={-1}>{title}</h1>
        <p>{subtitle}</p>
      </header>
      {children}
    </section>
  )
}
