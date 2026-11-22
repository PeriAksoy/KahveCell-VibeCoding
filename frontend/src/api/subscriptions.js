import { api, unwrap } from './client'

// Satıştaki paketler (giriş gerekmez).
export const listPlans = () => api.get('/subscriptions/plans').then(unwrap)

// Aktif aboneliği getirir; aktif abonelik yoksa null döner (hata değil, normal bir durum).
export async function getMySubscription() {
  try {
    return await api.get('/subscriptions/me').then(unwrap)
  } catch (error) {
    if (error?.response?.data?.error?.code === 'NO_ACTIVE_SUBSCRIPTION') return null
    throw error
  }
}

// Abonelik başlatır ve kartla ödeme alır. Dönen veri: { subscription, payment }
export const subscribe = (planCode, card) =>
  api.post('/subscriptions', { plan_code: planCode, card }).then(unwrap)

// Paketi yükseltir (kart gerekir, fiyat farkı tahsil edilir) veya düşürür (kart gerekmez).
export const changePlan = (planCode, card = null) =>
  api.patch('/subscriptions/me', { plan_code: planCode, card }).then(unwrap)

// Aboneliği iptal eder (anında geçerli).
export const cancelSubscription = () => api.delete('/subscriptions/me').then(unwrap)
