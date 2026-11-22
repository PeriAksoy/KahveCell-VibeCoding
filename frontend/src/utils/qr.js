const FIELDS = ['order_id', 'user_id', 'shop_id', 'created_at', 'signature']

// Kameradan okunan metni (QR'ın içindeki JSON) sipariş QR bilgisine çevirir.
// KahveCell QR'ı değilse okunabilir bir hata fırlatır.
export function parseQrContent(text) {
  let data
  try {
    data = JSON.parse(text)
  } catch {
    throw new Error('Bu bir KahveCell QR kodu değil.')
  }
  if (!data || typeof data !== 'object' || FIELDS.some((field) => typeof data[field] !== 'string')) {
    throw new Error('Bu bir KahveCell QR kodu değil.')
  }
  return Object.fromEntries(FIELDS.map((field) => [field, data[field]]))
}
