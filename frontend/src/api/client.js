import axios from 'axios'
import { useAuthStore } from '../store/authStore'

export const API_ORIGIN = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Bütün istekler bu nesne üzerinden gider: api.get('/shops'), api.post('/orders', {...})
export const api = axios.create({ baseURL: `${API_ORIGIN}/api/v1`, timeout: 15000 })

// Backend her cevabı { success, data, error } zarfında döner. Bu fonksiyon asıl veriyi (data) çıkarır.
export const unwrap = (response) => response.data.data

// Ekranda gösterilecek anlaşılır hata mesajı (backend Türkçe mesaj döner).
export function getErrorMessage(error) {
  return error?.response?.data?.error?.message ?? 'Sunucuya ulaşılamadı. Backend açık mı?'
}

// Backend ayakta mı? (ana sayfadaki bağlantı kontrolü için)
export async function checkBackend() {
  const response = await axios.get(`${API_ORIGIN}/`, { timeout: 5000 })
  return response.data.data.message
}

// Her isteğe giriş bileti (access token) eklenir.
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Bilet süresi dolduysa (401) yenileme bileti ile yeni bilet alıp isteği bir kez tekrar dener.
// Aynı anda birden çok istek patlarsa yenileme tek sefer yapılır.
let refreshing = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const { refreshToken, logout, setTokens } = useAuthStore.getState()
    const isAuthCall = config?.url?.startsWith('/auth/')

    if (response?.status !== 401 || !refreshToken || config._retried || isAuthCall) {
      throw error
    }
    config._retried = true
    try {
      refreshing ??= axios
        .post(`${API_ORIGIN}/api/v1/auth/refresh`, { refresh_token: refreshToken })
        .then((r) => setTokens(r.data.data))
        .finally(() => {
          refreshing = null
        })
      await refreshing
      return api(config)
    } catch {
      logout() // yenileme de başarısız: oturum bitti, kullanıcı giriş sayfasına yönlenir
      throw error
    }
  },
)
