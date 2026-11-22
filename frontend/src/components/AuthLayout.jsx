import { Link, Outlet } from 'react-router-dom'

// Giriş, kayıt ve kod ekranlarının ortak çerçevesi: ortada tek kart, etrafı boş.
export default function AuthLayout() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-brand">
          <span className="auth-brand-icon">☕</span>
          <span>KahveCell</span>
        </Link>
        <Outlet />
      </div>
    </div>
  )
}
