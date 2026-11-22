// Menü kategorileri (backend'in verdiği category değerine göre) ve ekranda görünme sırası.
export const CATEGORIES = [
  { key: 'espresso', label: 'Espresso Bazlı' },
  { key: 'filter', label: 'Filtre Kahveler' },
  { key: 'cold', label: 'Soğuk İçecekler' },
  { key: 'other', label: 'Diğer' },
]

// Sipariş özelleştirme seçenekleri (value'lar backend ile aynı olmalı).
export const SIZES = [
  { value: 'S', label: 'Küçük', hint: 'S' },
  { value: 'M', label: 'Orta', hint: 'M' },
  { value: 'L', label: 'Büyük', hint: 'L' },
]

export const MILK_TYPES = [
  { value: '', label: 'Sütsüz' },
  { value: 'whole', label: 'Tam yağlı süt' },
  { value: 'skim', label: 'Az yağlı süt' },
  { value: 'lactose_free', label: 'Laktozsuz süt' },
  { value: 'oat', label: 'Yulaf sütü' },
  { value: 'almond', label: 'Badem sütü' },
  { value: 'soy', label: 'Soya sütü' },
]

export const SUGAR_LEVELS = [
  { value: 0, label: 'Şekersiz' },
  { value: 1, label: '1 şeker' },
  { value: 2, label: '2 şeker' },
  { value: 3, label: '3 şeker' },
  { value: 4, label: '4 şeker' },
  { value: 5, label: '5 şeker' },
]

export const MAX_EXTRA_SHOTS = 4
