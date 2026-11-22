import { Route, Routes } from 'react-router-dom'
import AuthLayout from './components/AuthLayout'
import GuestOnly from './components/GuestOnly'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import RoleRoute from './components/RoleRoute'
import History from './pages/History'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Order from './pages/Order'
import QrCode from './pages/QrCode'
import Register from './pages/Register'
import ShopDetail from './pages/ShopDetail'
import ShopPanel from './pages/ShopPanel'
import Subscription from './pages/Subscription'
import VerifyOtp from './pages/VerifyOtp'

// Sayfa adresleri (URL) burada tanımlı.
export default function App() {
  return (
    <Routes>
      {/* Giriş, kayıt ve kod ekranları: menüsüz, ortada tek kart */}
      <Route element={<AuthLayout />}>
        <Route element={<GuestOnly />}>
          <Route path="/giris" element={<Login />} />
          <Route path="/kayit" element={<Register />} />
        </Route>
        <Route path="/dogrula" element={<VerifyOtp />} />
      </Route>

      {/* Uygulama sayfaları: üstte menü ile */}
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/dukkan/:shopId" element={<ShopDetail />} />

        {/* Giriş gerektiren sayfalar */}
        <Route element={<ProtectedRoute />}>
          <Route path="/siparis/:shopId/:productId" element={<Order />} />
          <Route path="/qr/:orderId" element={<QrCode />} />
          <Route path="/gecmis" element={<History />} />
          <Route path="/abonelik" element={<Subscription />} />
        </Route>

        {/* Yalnızca dükkân sahibi */}
        <Route element={<RoleRoute role="SHOP_OWNER" />}>
          <Route path="/panel" element={<ShopPanel />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
