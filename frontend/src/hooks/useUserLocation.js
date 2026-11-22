import { useEffect } from 'react'
import { useLocationStore } from '../store/locationStore'

// Kullanıcının konumunu verir; henüz istenmediyse tarayıcıdan izin ister.
// { status: 'loading' | 'gps' | 'fallback', reason, location: { lat, lng } | null }
export function useUserLocation() {
  const { status, reason, location, request } = useLocationStore()

  useEffect(() => {
    request()
  }, [request])

  return { status, reason, location }
}
