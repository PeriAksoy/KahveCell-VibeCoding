// 0.12 -> "120 m", 1.52 -> "1,5 km"
export function formatDistance(km) {
  if (km == null) return ''
  if (km < 1) return `${Math.round(km * 1000)} m`
  return `${km.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} km`
}

// 140 -> "140 ₺", 89.99 -> "89,99 ₺"
export function formatPrice(amount) {
  return `${Number(amount).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} ₺`
}

// Backend tarihleri saat dilimi olmadan (UTC) gönderebilir; "Z" ekleyerek doğru yorumlatıyoruz.
function parseUtc(isoString) {
  const hasZone = /[zZ]$|[+-]\d\d:\d\d$/.test(isoString)
  return new Date(hasZone ? isoString : `${isoString}Z`)
}

// "22.12.2026"
export function formatDate(isoString) {
  return parseUtc(isoString).toLocaleDateString('tr-TR')
}

// "22 Kas 2026 18:05" (kullanıcının yerel saatiyle)
export function formatDateTime(isoString) {
  return parseUtc(isoString).toLocaleString('tr-TR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// "az önce", "5 dk önce", "2 sa önce"; bir günden eskiyse tarih
export function formatRelative(isoString, now = Date.now()) {
  const minutes = Math.floor((now - parseUtc(isoString).getTime()) / 60000)
  if (minutes < 1) return 'az önce'
  if (minutes < 60) return `${minutes} dk önce`
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)} sa önce`
  return formatDate(isoString)
}
