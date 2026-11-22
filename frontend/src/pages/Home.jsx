import { useEffect, useMemo, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { listShops } from '../api/shops'
import ShopCard from '../components/ShopCard'
import ShopMap from '../components/ShopMap'
import { useUserLocation } from '../hooks/useUserLocation'
import { fold } from '../utils/text'

const LOCATION_NOTES = {
  loading: 'Konumunuz alınıyor…',
  gps: '📍 Konumunuz kullanılıyor.',
  denied: 'Konum izni verilmedi, Ankara Kızılay varsayıldı.',
  unavailable: 'Konumunuz alınamadı, Ankara Kızılay varsayıldı.',
  unsupported: 'Tarayıcınız konumu desteklemiyor, Ankara Kızılay varsayıldı.',
}

export default function Home() {
  const { status, reason, location } = useUserLocation()
  const [result, setResult] = useState({ key: null, items: [], error: '' })
  const [reloadKey, setReloadKey] = useState(0)
  const [query, setQuery] = useState('')

  // Hangi konum ve denemeyle istek atıldığını belirten anahtar. Sonuç bu anahtarla eşleşmiyorsa "yükleniyor"dur.
  const requestKey = location ? `${location.lat},${location.lng},${reloadKey}` : null
  const loading = status === 'loading' || (requestKey !== null && result.key !== requestKey)
  const shops = {
    state: loading ? 'loading' : result.error ? 'error' : 'ready',
    items: result.items,
    error: result.error,
  }

  // Konum belli olunca yakındaki dükkânları (mesafeye göre sıralı) çek.
  useEffect(() => {
    if (!location) return
    let cancelled = false
    listShops(location)
      .then((items) => !cancelled && setResult({ key: requestKey, items, error: '' }))
      .catch((error) => !cancelled && setResult({ key: requestKey, items: [], error: getErrorMessage(error) }))
    return () => {
      cancelled = true
    }
  }, [location, requestKey])

  // Arama: yazdıkça isim veya adreste filtreler (Türkçe karakter ve büyük/küçük harf fark etmez).
  const visible = useMemo(() => {
    const needle = fold(query.trim())
    if (!needle) return result.items
    return result.items.filter((s) => fold(s.name).includes(needle) || fold(s.address).includes(needle))
  }, [result.items, query])

  const locationNote = LOCATION_NOTES[status === 'fallback' ? reason : status]

  return (
    <>
      <div className="home-top">
        <div>
          <h1>Yakındaki dükkânlar</h1>
          <p className="muted">{locationNote}</p>
        </div>
        <input
          type="search"
          className="search-input"
          placeholder="Dükkân adı veya adres ara…"
          aria-label="Dükkân ara"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="home-grid">
        <section className="home-list" aria-label="Dükkân listesi">
          {shops.state === 'loading' && <p className="muted">Dükkânlar yükleniyor…</p>}

          {shops.state === 'error' && (
            <div className="alert alert-error">
              {shops.error}{' '}
              <button type="button" className="link-button" onClick={() => setReloadKey((k) => k + 1)}>
                Tekrar dene
              </button>
            </div>
          )}

          {shops.state === 'ready' && shops.items.length === 0 && (
            <p className="muted">Henüz kayıtlı dükkân yok.</p>
          )}

          {shops.state === 'ready' && shops.items.length > 0 && visible.length === 0 && (
            <p className="muted">“{query}” için dükkân bulunamadı.</p>
          )}

          {visible.map((shop) => (
            <ShopCard key={shop.id} shop={shop} />
          ))}
        </section>

        <section className="home-map" aria-label="Harita">
          {location ? <ShopMap shops={visible} userLocation={location} /> : <div className="map map-placeholder" />}
        </section>
      </div>
    </>
  )
}
