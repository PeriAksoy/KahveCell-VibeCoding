import { Link } from 'react-router-dom'
import { formatDistance } from '../utils/format'

// Dükkân listesindeki tek bir kart.
export default function ShopCard({ shop }) {
  return (
    <article className="shop-card">
      <div className="shop-card-head">
        <h3>{shop.name}</h3>
        <span className={`badge ${shop.is_open ? 'badge-open' : 'badge-closed'}`}>
          {shop.is_open ? 'Açık' : 'Kapalı'}
        </span>
      </div>
      <p className="shop-card-address">{shop.address}</p>
      <div className="shop-card-meta">
        <span title="Puan">★ {shop.rating.toFixed(1)}</span>
        {shop.distance_km != null && <span title="Mesafe">📍 {formatDistance(shop.distance_km)}</span>}
        <span className="muted" title="Çalışma saatleri">
          {shop.opens_at}–{shop.closes_at}
        </span>
      </div>
      <Link to={`/dukkan/${shop.id}`} className="button button-block">
        Menüyü Gör
      </Link>
    </article>
  )
}
