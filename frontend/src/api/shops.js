import { api, unwrap } from './client'

// Dükkânları getirir. Konum verilirse her dükkânda distance_km dolu gelir ve en yakın olan başta olur.
export async function listShops({ lat, lng }) {
  const data = await api.get('/shops', { params: { lat, lng, limit: 200 } }).then(unwrap)
  return data.items
}

// Tek dükkân + menüsü. Konum verilirse distance_km dolu gelir.
export const getShop = (shopId, location) =>
  api.get(`/shops/${shopId}`, { params: location ? { lat: location.lat, lng: location.lng } : {} }).then(unwrap)
