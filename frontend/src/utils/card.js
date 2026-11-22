export const TEST_CARD = '4242 4242 4242 4242'

// Yazarken kart numarasını 4'lü gruplar: "4242424242424242" -> "4242 4242 4242 4242"
export function formatCardNumber(raw) {
  return raw
    .replace(/\D/g, '')
    .slice(0, 16)
    .replace(/(.{4})/g, '$1 ')
    .trim()
}

// Kart formunu kontrol eder. Hata yoksa boş nesne döner; varsa alan adına göre mesaj verir.
// Kurallar backend ile aynıdır (16 hane, geçmemiş tarih, 3-4 haneli CVC).
export function validateCard({ holder, number, month, year, cvc }, now = new Date()) {
  const errors = {}
  if (holder.trim().length < 2) errors.holder = 'Kart üzerindeki ismi girin.'
  if (number.replace(/\D/g, '').length !== 16) errors.number = 'Kart numarası 16 haneli olmalı.'

  const m = Number(month)
  const y = Number(year)
  if (!Number.isInteger(m) || m < 1 || m > 12 || !Number.isInteger(y) || y < 2000) {
    errors.expiry = 'Geçerli bir son kullanma tarihi girin (ay 1-12, yıl 4 haneli).'
  } else if (y < now.getFullYear() || (y === now.getFullYear() && m < now.getMonth() + 1)) {
    errors.expiry = 'Kartın son kullanma tarihi geçmiş.'
  }

  if (!/^\d{3,4}$/.test(cvc)) errors.cvc = 'CVC 3 veya 4 haneli olmalı.'
  return errors
}

// Formdaki değerleri backend'in beklediği biçime çevirir.
export const toCardPayload = ({ holder, number, month, year, cvc }) => ({
  card_holder: holder.trim(),
  card_number: number,
  expiry_month: Number(month),
  expiry_year: Number(year),
  cvc,
})
