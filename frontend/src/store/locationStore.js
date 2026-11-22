import { create } from 'zustand'

// İzin verilmezse veya konum alınamazsa kullanılacak varsayılan konum: Ankara Kızılay Meydanı.
export const DEFAULT_LOCATION = { lat: 39.92, lng: 32.855 }

const supported = typeof navigator !== 'undefined' && 'geolocation' in navigator

// Kullanıcının konumu uygulama genelinde TEK sefer istenir ve burada saklanır;
// ana sayfadan dükkân detayına geçince izin yeniden sorulmaz.
// status: 'loading' | 'gps' (gerçek konum) | 'fallback' (varsayılan; reason: denied | unavailable | unsupported)
export const useLocationStore = create((set, get) => ({
  status: supported ? 'loading' : 'fallback',
  location: supported ? null : DEFAULT_LOCATION,
  reason: supported ? null : 'unsupported',
  requested: false,

  request: () => {
    if (get().requested || !supported) return
    set({ requested: true })
    navigator.geolocation.getCurrentPosition(
      (position) =>
        set({
          status: 'gps',
          location: { lat: position.coords.latitude, lng: position.coords.longitude },
        }),
      (error) =>
        set({
          status: 'fallback',
          location: DEFAULT_LOCATION,
          reason: error.code === error.PERMISSION_DENIED ? 'denied' : 'unavailable',
        }),
      { timeout: 8000, maximumAge: 5 * 60 * 1000 },
    )
  },
}))
