import { api, unwrap } from './client'

// Sipariş verir (abonelikten 1 hak düşer). Dönen veri: { order, remaining_credits }
export const createOrder = (body) => api.post('/orders', body).then(unwrap)

// Tek sipariş (QR dahil). Durumu takip etmek için tekrar tekrar çağrılır.
export const getOrder = (orderId) => api.get(`/orders/${orderId}`).then(unwrap)

// Sipariş geçmişim, en yeniden eskiye.
export const listMyOrders = ({ limit, offset }) =>
  api.get('/orders/history', { params: { limit, offset } }).then(unwrap)

// Dükkân kabul etmeden önce siparişi iptal eder (hak iade edilir).
export const cancelOrder = (orderId) => api.post(`/orders/${orderId}/cancel`).then(unwrap)

// ---- Dükkân sahibi ----

// Dükkânımın bitmemiş siparişleri (bekleyen, kabul, hazırlanıyor, hazır). Öncelikli müşteriler önde, sonra en eski.
export const listShopOrders = () => api.get('/orders/shop', { params: { limit: 200 } }).then(unwrap)

// Sipariş durumunu ilerletir. Teslim (COMPLETED) için müşterinin QR içeriği (qr) zorunludur.
export const updateOrderStatus = (orderId, status, qr = null) =>
  api.patch(`/orders/${orderId}/status`, { status, qr }).then(unwrap)

// QR kodun gerçek olup olmadığını kontrol eder (durumu değiştirmez).
// Dönen veri: { authentic, can_deliver, message, order }
export const verifyQr = (qr) => api.post('/orders/verify-qr', { qr }).then(unwrap)
