import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { getShop } from '../api/shops'
import { CATEGORIES } from '../constants/menu'
import { useUserLocation } from '../hooks/useUserLocation'
import { formatDistance, formatPrice } from '../utils/format'

export default function ShopDetail() {
  const { shopId } = useParams()
  const { status, location } = useUserLocation()
  const [result, setResult] = useState({ key: null, shop: null, error: '' })
  const [reloadKey, setReloadKey] = useState(0)

  // Mesafe için konum belli olunca (ana sayfadan geldiysen zaten belli) dükkânı çek.
  const requestKey = status === 'loading' ? null : `${shopId}|${reloadKey}`
  const loading = requestKey === null || result.key !== requestKey

  useEffect(() => {
    if (requestKey === null) return
    let cancelled = false
    getShop(shopId, location)
      .then((shop) => !cancelled && setResult({ key: requestKey, shop, error: '' }))
      .catch((error) => {
        if (cancelled) return
        const missing = [404, 422].includes(error?.response?.status)
        setResult({ key: requestKey, shop: null, error: missing ? 'Dükkân bulunamadı.' : getErrorMessage(error) })
      })
    return () => {
      cancelled = true
    }
  }, [shopId, requestKey, location])

  const { shop } = result
  // Menüyü kategorilere ayır, boş kategorileri gösterme.
  const groups = useMemo(() => {
    if (!shop) return []
    return CATEGORIES.map((c) => ({ ...c, items: shop.menu.filter((p) => p.category === c.key) })).filter(
      (g) => g.items.length > 0,
    )
  }, [shop])

  return (
    <div className="page-narrow">
      <Link to="/" className="back-link">
        ← Dükkânlara dön
      </Link>

      {loading && <p className="muted">Dükkân yükleniyor…</p>}

      {!loading && result.error && (
        <div className="alert alert-error">
          {result.error}{' '}
          <button type="button" className="link-button" onClick={() => setReloadKey((k) => k + 1)}>
            Tekrar dene
          </button>
        </div>
      )}

      {!loading && shop && (
        <>
          <section className="shop-hero">
            <div className="shop-card-head">
              <h1>{shop.name}</h1>
              <span className={`badge ${shop.is_open ? 'badge-open' : 'badge-closed'}`}>
                {shop.is_open ? 'Açık' : 'Kapalı'}
              </span>
            </div>
            <p className="shop-card-address">{shop.address}</p>
            <div className="shop-card-meta">
              <span title="Çalışma saatleri">🕒 {shop.opens_at}–{shop.closes_at}</span>
              <span title="Puan">★ {shop.rating.toFixed(1)}</span>
              {shop.distance_km != null && <span title="Mesafe">📍 {formatDistance(shop.distance_km)}</span>}
            </div>
          </section>

          {groups.length === 0 && <p className="muted">Bu dükkânın menüsü henüz boş.</p>}

          {groups.map((group) => (
            <section key={group.key}>
              <h2>{group.label}</h2>
              <ul className="menu-list">
                {group.items.map((product) => (
                  <li key={product.id} className="menu-item">
                    <div className="menu-item-info">
                      <strong>{product.name}</strong>
                      {product.description && <p className="muted">{product.description}</p>}
                      <span className="small muted">Liste fiyatı: {formatPrice(product.base_price)}</span>
                    </div>
                    {product.is_available ? (
                      <Link to={`/siparis/${shop.id}/${product.id}`} className="button">
                        Sipariş Ver
                      </Link>
                    ) : (
                      <button type="button" className="button" disabled>
                        Satışta değil
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </>
      )}
    </div>
  )
}
