import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { cancelOrder, getOrder } from '../api/orders'
import { FINAL_STATUSES, ORDER_STATUS, PROGRESS_STEPS, statusInfo } from '../constants/orderStatus'
import { formatDateTime } from '../utils/format'
import { describeOptions } from '../utils/order'

const POLL_MS = 4000 // durum kaç milisaniyede bir sorulur

export default function QrCode() {
  const { orderId } = useParams()
  const location = useLocation()

  // Sipariş ekranından geldiysek sipariş hazır elimizde: QR hemen görünür, sonra güncellenir.
  const initial = location.state?.order?.id === orderId ? location.state.order : null
  const [order, setOrder] = useState(initial)
  const [fatal, setFatal] = useState({ id: null, message: '' })
  const [connectionLost, setConnectionLost] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [actionError, setActionError] = useState('')

  // Durumu birkaç saniyede bir backend'e sorar; sipariş teslim edilince veya iptal olunca durur.
  // (Her istek bitince bir sonraki planlanır, böylece yavaş bağlantıda istekler üst üste binmez.)
  useEffect(() => {
    let cancelled = false
    let timer

    async function poll() {
      try {
        const fresh = await getOrder(orderId)
        if (cancelled) return
        setOrder(fresh)
        setConnectionLost(false)
        if (FINAL_STATUSES.includes(fresh.status)) return
      } catch (error) {
        if (cancelled) return
        if ([404, 422].includes(error?.response?.status)) {
          setFatal({ id: orderId, message: 'Sipariş bulunamadı.' })
          return
        }
        setConnectionLost(true) // geçici sorun: eldeki bilgiyi koru, yeniden dene
      }
      timer = setTimeout(poll, POLL_MS)
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [orderId])

  async function handleCancel() {
    if (!window.confirm('Siparişi iptal etmek istediğine emin misin?')) return
    setCancelling(true)
    setActionError('')
    try {
      setOrder(await cancelOrder(orderId))
    } catch (error) {
      setActionError(getErrorMessage(error))
    } finally {
      setCancelling(false)
    }
  }

  const current = order?.id === orderId ? order : null
  const fatalMessage = fatal.id === orderId ? fatal.message : ''

  if (fatalMessage) {
    return (
      <div className="page-narrow">
        <div className="alert alert-error">{fatalMessage}</div>
        <Link to="/gecmis">← Sipariş geçmişim</Link>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="page-narrow">
        <p className="muted">Sipariş yükleniyor…</p>
      </div>
    )
  }

  const info = statusInfo(current.status)
  const completed = current.status === 'COMPLETED'
  const cancelled = current.status === 'CANCELLED'
  const showQr = !completed && !cancelled
  const stepIndex = PROGRESS_STEPS.indexOf(current.status)

  return (
    <div className="page-narrow qr-page">
      {showQr && (
        <section className={`qr-card tone-${info.tone}`}>
          <p className="qr-hint">Teslim alırken bu kodu dükkânda göster</p>
          <img className="qr-image" src={current.qr_image} alt="Sipariş QR kodu" />
        </section>
      )}

      {completed && (
        <section className="celebration tone-completed">
          <div className="celebration-icon">☕</div>
          <h1>Afiyet olsun!</h1>
          <p>Siparişini teslim aldın. Keyifli bir kahve molası dileriz.</p>
        </section>
      )}

      {cancelled && (
        <section className="cancelled-box tone-cancelled">
          <h1>Siparişin iptal edildi</h1>
          <p>Kullandığın kahve hakkı hesabına iade edilir.</p>
        </section>
      )}

      {/* Durum: değiştikçe key değişir, animasyon yeniden oynar; rengi duruma göre değişir. */}
      <div key={current.status} className={`status-banner tone-${info.tone}`} aria-live="polite">
        <span className="status-banner-icon">{info.icon}</span>
        <div>
          <strong className="status-banner-label">{info.label}</strong>
          {info.message && <p>{info.message}</p>}
        </div>
      </div>

      {showQr && stepIndex >= 0 && (
        <ol className="progress">
          {PROGRESS_STEPS.map((step, index) => (
            <li
              key={step}
              className={`progress-step ${index <= stepIndex ? 'progress-step-done' : ''} ${
                index === stepIndex ? `progress-step-current tone-${info.tone}` : ''
              }`}
            >
              <span className="progress-dot" />
              <span className="progress-label">{ORDER_STATUS[step].label}</span>
            </li>
          ))}
        </ol>
      )}

      {connectionLost && <p className="muted small">Bağlantı sorunu, yeniden deneniyor…</p>}

      <section className="order-summary">
        <h2>Sipariş özeti</h2>
        <dl>
          <dt>Ürün</dt>
          <dd>{current.product.name}</dd>
          <dt>Seçimler</dt>
          <dd>{describeOptions(current)}</dd>
          <dt>Dükkân</dt>
          <dd>
            {current.shop.name}
            <br />
            <span className="muted small">{current.shop.address}</span>
          </dd>
          <dt>Sipariş zamanı</dt>
          <dd>{formatDateTime(current.created_at)}</dd>
        </dl>
      </section>

      {actionError && <div className="alert alert-error">{actionError}</div>}

      {current.status === 'PENDING' && (
        <button type="button" className="button button-block button-secondary" onClick={handleCancel} disabled={cancelling}>
          {cancelling ? 'İptal ediliyor…' : 'Siparişi iptal et'}
        </button>
      )}

      {(completed || cancelled) && (
        <Link to="/" className="button button-block">
          Yeni sipariş ver
        </Link>
      )}
      <p className="qr-footer">
        <Link to="/gecmis">Sipariş geçmişim</Link>
      </p>
    </div>
  )
}
