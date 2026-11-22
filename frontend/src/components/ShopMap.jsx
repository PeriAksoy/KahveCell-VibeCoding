import L from 'leaflet'
import { useEffect, useMemo } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'

// Dükkân pini: kahverengi daire içinde kahve fincanı. Kullanıcı: mavi nokta (farklı renk).
const shopIcon = L.divIcon({
  className: 'shop-pin',
  html: '☕',
  iconSize: [34, 34],
  iconAnchor: [17, 17],
  popupAnchor: [0, -18],
})

const userIcon = L.divIcon({
  className: 'user-pin',
  html: '<span></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -12],
})

// Harita, kullanıcıyı ve gösterilen dükkânları kapsayacak şekilde otomatik yakınlaşır.
function FitBounds({ points }) {
  const map = useMap()

  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 14)
    else map.fitBounds(points, { padding: [40, 40], maxZoom: 15 })
  }, [points, map])

  return null
}

export default function ShopMap({ shops, userLocation }) {
  const userPoint = useMemo(() => [userLocation.lat, userLocation.lng], [userLocation])
  const points = useMemo(
    () => [userPoint, ...shops.map((s) => [s.latitude, s.longitude])],
    [userPoint, shops],
  )

  return (
    <MapContainer center={userPoint} zoom={13} className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={points} />

      <Marker position={userPoint} icon={userIcon} zIndexOffset={1000}>
        <Popup>Konumunuz</Popup>
      </Marker>

      {shops.map((shop) => (
        <Marker key={shop.id} position={[shop.latitude, shop.longitude]} icon={shopIcon}>
          <Popup>
            <strong>{shop.name}</strong>
            <br />
            {shop.address}
            <br />
            <Link to={`/dukkan/${shop.id}`}>Menüyü gör</Link>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
