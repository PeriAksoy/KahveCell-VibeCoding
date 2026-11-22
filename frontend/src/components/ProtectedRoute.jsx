import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

// Giriş gerektiren sayfaları sarar. Giriş yoksa giriş sayfasına yollar,
// giriş yapınca kullanıcı geldiği sayfaya döner.
export default function ProtectedRoute() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const location = useLocation()

  if (!accessToken) {
    return <Navigate to="/giris" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}
