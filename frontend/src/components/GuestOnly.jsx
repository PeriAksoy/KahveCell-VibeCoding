import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { homeFor } from '../utils/roles'

// Giriş ve kayıt sayfalarını sarar: zaten giriş yapmış kullanıcı bu sayfaları görmez, kendi ana sayfasına gider.
export default function GuestOnly() {
  const { accessToken, user } = useAuthStore()
  return accessToken ? <Navigate to={homeFor(user)} replace /> : <Outlet />
}
