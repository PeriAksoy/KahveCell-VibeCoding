import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/authStore'

// Bütün sayfaların ortak çerçevesi: üstte menü, altında sayfanın kendisi.
export default function Layout() {
  const { accessToken, refreshToken, user, logout } = useAuthStore()
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken })
    } catch {
      // Backend'e ulaşılamasa bile bu cihazdaki oturumu kapatıyoruz.
    }
    logout()
    navigate('/')
  }

  return (
    <>
      <header className="header">
        <div className="container header-inner">
          <NavLink to="/" className="brand">
            ☕ KahveCell
          </NavLink>
          <nav className="nav">
            <NavLink to="/" end>Ana sayfa</NavLink>
            {user?.role === 'SHOP_OWNER' ? (
              <NavLink to="/panel">Sipariş paneli</NavLink>
            ) : (
              <>
                <NavLink to="/gecmis">Geçmiş</NavLink>
                <NavLink to="/abonelik">Abonelik</NavLink>
              </>
            )}
            {accessToken ? (
              <>
                <span className="muted">{user?.full_name ?? user?.phone_number}</span>
                <button type="button" className="link-button" onClick={handleLogout}>
                  Çıkış
                </button>
              </>
            ) : (
              <>
                <NavLink to="/giris">Giriş</NavLink>
                <NavLink to="/kayit">Kayıt</NavLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="container main">
        <Outlet />
      </main>
    </>
  )
}
