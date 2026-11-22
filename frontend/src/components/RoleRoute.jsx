import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

// Yalnızca belirli rolün girebildiği sayfaları sarar (örn. dükkân paneli).
// Giriş yoksa giriş sayfasına, rol uymuyorsa ana sayfaya yollar.
// NOT: Bu yalnızca arayüz koruması; asıl yetki kontrolünü backend yapar (yanlış rolle istek atılırsa 403 verir).
export default function RoleRoute({ role }) {
  const { accessToken, user } = useAuthStore()
  const location = useLocation()

  if (!accessToken) return <Navigate to="/giris" replace state={{ from: location.pathname }} />
  if (user?.role !== role) return <Navigate to="/" replace />
  return <Outlet />
}
