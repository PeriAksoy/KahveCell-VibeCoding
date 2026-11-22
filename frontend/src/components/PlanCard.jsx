import { formatPrice } from '../utils/format'

// Paketin özellik listesi
function features(plan) {
  const list = [plan.is_unlimited ? 'Sınırsız kahve' : `Ayda ${plan.monthly_credits} kahve`, 'Tüm dükkânlarda geçerli']
  if (plan.guest_passes > 0) list.push(`${plan.guest_passes} misafir hakkı`)
  if (plan.has_priority) list.push('Öncelikli sipariş')
  return list
}

// Tek bir paket kartı. action: { label, disabled } — buton yazısı ve durumu üst sayfadan gelir.
export default function PlanCard({ plan, current, action, onSelect }) {
  return (
    <article className={`plan-card ${current ? 'plan-card-current' : ''}`}>
      {current && <span className="plan-flag">Mevcut paketin</span>}
      <h3>{plan.name}</h3>
      <p className="plan-price">
        <strong>{formatPrice(plan.monthly_price)}</strong>
        <span className="muted"> / ay</span>
      </p>
      <ul className="plan-features">
        {features(plan).map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
      <button type="button" className="button button-block" disabled={action.disabled} onClick={() => onSelect(plan)}>
        {action.label}
      </button>
    </article>
  )
}
