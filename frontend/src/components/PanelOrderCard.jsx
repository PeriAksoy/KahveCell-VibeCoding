import { formatDateTime, formatRelative } from '../utils/format'
import { describeOptions } from '../utils/order'

// Dükkân panelindeki tek sipariş kartı: müşteri, ürün, özelleştirmeler, zaman ve duruma göre tek buton.
export default function PanelOrderCard({ order, action, busy, onAction }) {
  return (
    <article className="panel-order">
      <div className="panel-order-head">
        <div>
          <strong className="panel-customer">{order.customer_name}</strong>
          {order.is_priority && <span className="badge badge-priority">⭐ Öncelikli</span>}
        </div>
        <span className="muted small" title={formatDateTime(order.created_at)}>
          {formatRelative(order.created_at)}
        </span>
      </div>

      <p className="panel-product">{order.product.name}</p>
      <p className="panel-options">{describeOptions(order)}</p>
      <p className="muted small">
        Sipariş zamanı: {formatDateTime(order.created_at)}
        <br />
        {order.shop.name}
      </p>

      <button type="button" className="button button-block" disabled={busy} onClick={() => onAction(order)}>
        {busy ? 'İşleniyor…' : action.label}
      </button>
    </article>
  )
}
