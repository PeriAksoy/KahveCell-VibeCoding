// Sipariş durumları: ekranda görünen ad, simge, renk tonu (CSS'te tone-* sınıfları) ve açıklama.
export const ORDER_STATUS = {
  PENDING: { label: 'Bekliyor', icon: '⏳', tone: 'pending', message: 'Siparişin dükkâna iletildi, onay bekleniyor.' },
  ACCEPTED: { label: 'Kabul Edildi', icon: '👍', tone: 'accepted', message: 'Dükkân siparişini kabul etti.' },
  PREPARING: { label: 'Hazırlanıyor', icon: '☕', tone: 'preparing', message: 'Kahven hazırlanıyor…' },
  READY: { label: 'Hazır', icon: '✅', tone: 'ready', message: 'Kahven hazır! QR kodu dükkânda göster.' },
  COMPLETED: { label: 'Teslim Edildi', icon: '🎉', tone: 'completed', message: '' },
  CANCELLED: { label: 'İptal Edildi', icon: '✕', tone: 'cancelled', message: '' },
}

// İlerleme çubuğundaki adımlar (teslim ve iptal ayrı ekranlarla gösterilir).
export const PROGRESS_STEPS = ['PENDING', 'ACCEPTED', 'PREPARING', 'READY']

// Bu durumlara gelince sipariş artık değişmez, durum sorgulamayı bırakırız.
export const FINAL_STATUSES = ['COMPLETED', 'CANCELLED']

export const statusInfo = (status) =>
  ORDER_STATUS[status] ?? { label: status, icon: '', tone: 'pending', message: '' }

// Dükkân panelindeki sekmeler. action: o sekmedeki siparişlerin butonu.
//   next: butona basınca geçilecek durum; scan: true ise kamera ile QR okutma penceresi açılır.
export const PANEL_TABS = [
  { status: 'PENDING', label: 'Bekleyen', empty: 'Bekleyen sipariş yok.', action: { label: 'Kabul Et', next: 'ACCEPTED' } },
  { status: 'ACCEPTED', label: 'Kabul Edilen', empty: 'Kabul edilmiş sipariş yok.', action: { label: 'Hazırlamaya Başla', next: 'PREPARING' } },
  { status: 'PREPARING', label: 'Hazırlanıyor', empty: 'Hazırlanan sipariş yok.', action: { label: 'Hazır', next: 'READY' } },
  { status: 'READY', label: 'Hazır', empty: 'Teslim bekleyen sipariş yok.', action: { label: '📷 QR Okut', scan: true } },
]
