import { statusInfo } from '../constants/orderStatus'

// Sipariş durumunu renkli küçük bir etiket olarak gösterir.
export default function StatusPill({ status }) {
  const info = statusInfo(status)
  return (
    <span className={`status-pill tone-${info.tone}`}>
      {info.icon} {info.label}
    </span>
  )
}
