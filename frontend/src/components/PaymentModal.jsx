import { useState } from 'react'
import { getErrorMessage } from '../api/client'
import { changePlan, subscribe } from '../api/subscriptions'
import { formatCardNumber, TEST_CARD, toCardPayload, validateCard } from '../utils/card'
import { formatPrice } from '../utils/format'
import Modal from './Modal'

// Kart bilgisi penceresi. mode: 'subscribe' (yeni abonelik) veya 'upgrade' (paket yükseltme, fark ücreti).
// Ödeme başarılıysa onSuccess(sonuç) çağrılır; başarısızsa hata pencerede kalır, kullanıcı tekrar deneyebilir.
export default function PaymentModal({ plan, mode, amount, onClose, onSuccess }) {
  // Test kolaylığı için form hazır dolu gelir (kart numarası: her zaman başarılı olan test kartı).
  const [form, setForm] = useState(() => ({
    holder: 'Test Kullanıcı',
    number: TEST_CARD,
    month: '12',
    year: String(new Date().getFullYear() + 4),
    cvc: '123',
  }))
  const [errors, setErrors] = useState({})
  const [submitError, setSubmitError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const set = (field) => (event) => setForm((f) => ({ ...f, [field]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    const found = validateCard(form)
    setErrors(found)
    setSubmitError('')
    if (Object.keys(found).length > 0) return

    setSubmitting(true)
    try {
      const card = toCardPayload(form)
      const result = mode === 'upgrade' ? await changePlan(plan.code, card) : await subscribe(plan.code, card)
      onSuccess(result)
    } catch (error) {
      const failed = error?.response?.data?.error?.code === 'PAYMENT_FAILED'
      const message = getErrorMessage(error)
      setSubmitError(failed ? `Ödeme başarısız. ${message}` : message)
      setSubmitting(false)
    }
  }

  const title = mode === 'upgrade' ? `${plan.name} paketine yükselt` : `${plan.name} paketini satın al`

  return (
    <Modal title={title} onClose={onClose} busy={submitting}>
      <div className="pay-summary">
        <span>{mode === 'upgrade' ? 'Fark ücreti' : `${plan.name} · aylık`}</span>
        <strong>{formatPrice(amount)}</strong>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="card-holder">Kart üzerindeki isim</label>
          <input id="card-holder" type="text" autoComplete="cc-name" value={form.holder} onChange={set('holder')} />
          {errors.holder && <p className="field-error">{errors.holder}</p>}
        </div>

        <div className="field">
          <label htmlFor="card-number">Kart numarası</label>
          <input
            id="card-number"
            type="text"
            inputMode="numeric"
            autoComplete="cc-number"
            value={form.number}
            onChange={(e) => setForm((f) => ({ ...f, number: formatCardNumber(e.target.value) }))}
          />
          <p className="field-hint">Test kartı, değiştirmeyin</p>
          {errors.number && <p className="field-error">{errors.number}</p>}
        </div>

        <div className="card-row">
          <div className="field">
            <label htmlFor="card-month">Ay</label>
            <input id="card-month" type="text" inputMode="numeric" maxLength={2} autoComplete="cc-exp-month" value={form.month} onChange={set('month')} />
          </div>
          <div className="field">
            <label htmlFor="card-year">Yıl</label>
            <input id="card-year" type="text" inputMode="numeric" maxLength={4} autoComplete="cc-exp-year" value={form.year} onChange={set('year')} />
          </div>
          <div className="field">
            <label htmlFor="card-cvc">CVC</label>
            <input id="card-cvc" type="text" inputMode="numeric" maxLength={4} autoComplete="cc-csc" value={form.cvc} onChange={set('cvc')} />
          </div>
        </div>
        {errors.expiry && <p className="field-error card-error">{errors.expiry}</p>}
        {errors.cvc && <p className="field-error card-error">{errors.cvc}</p>}

        {submitError && <div className="alert alert-error">{submitError}</div>}

        <div className="modal-actions">
          <button type="button" className="button button-secondary" onClick={onClose} disabled={submitting}>
            Vazgeç
          </button>
          <button type="submit" className="button" disabled={submitting}>
            {submitting ? 'Ödeme alınıyor…' : `Öde ${formatPrice(amount)}`}
          </button>
        </div>
      </form>
    </Modal>
  )
}
