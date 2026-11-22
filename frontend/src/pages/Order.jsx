import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { createOrder } from '../api/orders'
import { getShop } from '../api/shops'
import { getMySubscription } from '../api/subscriptions'
import { MAX_EXTRA_SHOTS, MILK_TYPES, SIZES, SUGAR_LEVELS } from '../constants/menu'
import { formatDate, formatPrice } from '../utils/format'

export default function Order() {
  const { shopId, productId } = useParams()
  const navigate = useNavigate()

  // Sayfa verisi: dükkân (menüsüyle) ve aktif abonelik
  const [data, setData] = useState({ key: null, shop: null, subscription: null, error: '' })
  const [reloadKey, setReloadKey] = useState(0)
  // Kullanıcının seçimleri
  const [size, setSize] = useState('M')
  const [milk, setMilk] = useState('')
  const [sugar, setSugar] = useState(0)
  const [shots, setShots] = useState(0)
  // Onaylama durumu
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const requestKey = `${shopId}|${reloadKey}`
  const loading = data.key !== requestKey

  useEffect(() => {
    let cancelled = false
    Promise.all([getShop(shopId), getMySubscription()])
      .then(([shop, subscription]) => !cancelled && setData({ key: requestKey, shop, subscription, error: '' }))
      .catch((error) => {
        if (cancelled) return
        const status = error?.response?.status
        let message = getErrorMessage(error)
        if ([404, 422].includes(status)) message = 'Dükkân bulunamadı.'
        if (status === 403) message = 'Sipariş verebilmek için müşteri hesabıyla giriş yapmalısınız.'
        setData({ key: requestKey, shop: null, subscription: null, error: message })
      })
    return () => {
      cancelled = true
    }
  }, [shopId, requestKey])

  async function handleConfirm() {
    setSubmitting(true)
    setSubmitError('')
    try {
      const result = await createOrder({
        shop_id: shopId,
        product_id: productId,
        size,
        sugar_level: sugar,
        milk_type: milk || null,
        extra_shots: shots,
      })
      navigate(`/qr/${result.order.id}`, {
        state: { order: result.order, remainingCredits: result.remaining_credits },
      })
    } catch (error) {
      setSubmitError(getErrorMessage(error))
      const code = error?.response?.data?.error?.code
      // Bu arada hak bittiyse veya abonelik değiştiyse güncel durumu yeniden çek.
      if (code === 'NO_CREDITS_LEFT' || code === 'SUBSCRIPTION_REQUIRED') setReloadKey((k) => k + 1)
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="page-narrow">
        <p className="muted">Yükleniyor…</p>
      </div>
    )
  }

  const { shop, subscription } = data
  const product = shop?.menu.find((p) => p.id === productId)

  if (data.error || !product) {
    return (
      <div className="page-narrow">
        <Link to={shop ? `/dukkan/${shop.id}` : '/'} className="back-link">
          ← Geri dön
        </Link>
        <div className="alert alert-error">
          {data.error || 'Bu ürün bu dükkânın menüsünde bulunamadı.'}{' '}
          {data.error && (
            <button type="button" className="link-button" onClick={() => setReloadKey((k) => k + 1)}>
              Tekrar dene
            </button>
          )}
        </div>
      </div>
    )
  }

  // ---- kredi durumu ----
  const hasSubscription = subscription !== null
  const unlimited = hasSubscription && subscription.is_unlimited
  const remaining = hasSubscription && !unlimited ? subscription.remaining_credits : null
  const outOfCredits = hasSubscription && !unlimited && remaining <= 0
  const creditsAfter = remaining === null ? null : remaining - 1
  const canOrder = hasSubscription && !outOfCredits && product.is_available && !submitting

  return (
    <div className="page-narrow">
      <Link to={`/dukkan/${shop.id}`} className="back-link">
        ← {shop.name}
      </Link>

      <h1>Siparişini hazırla</h1>

      {/* Seçilen ürün */}
      <section className="order-product">
        <div>
          <strong className="order-product-name">{product.name}</strong>
          {product.description && <p className="muted">{product.description}</p>}
          <span className="small muted">
            {shop.name} · Liste fiyatı: {formatPrice(product.base_price)}
          </span>
        </div>
      </section>

      {!shop.is_open && (
        <div className="alert alert-info">
          Bu dükkân şu an kapalı görünüyor ({shop.opens_at}–{shop.closes_at}). Siparişin dükkân açılınca hazırlanır.
        </div>
      )}

      {/* Özelleştirmeler */}
      <section className="order-options">
        <fieldset className="option-group">
          <legend>Boyut</legend>
          <div className="segmented">
            {SIZES.map((s) => (
              <label key={s.value} className={`segment ${size === s.value ? 'segment-active' : ''}`}>
                <input
                  type="radio"
                  name="size"
                  value={s.value}
                  checked={size === s.value}
                  onChange={() => setSize(s.value)}
                  className="visually-hidden"
                />
                <strong>{s.hint}</strong>
                <span>{s.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="option-row">
          <div className="field">
            <label htmlFor="milk">Süt tipi</label>
            <select id="milk" value={milk} onChange={(e) => setMilk(e.target.value)}>
              {MILK_TYPES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="sugar">Şeker</label>
            <select id="sugar" value={sugar} onChange={(e) => setSugar(Number(e.target.value))}>
              {SUGAR_LEVELS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <span className="field-label">Ek shot</span>
          <div className="stepper">
            <button
              type="button"
              className="stepper-button"
              onClick={() => setShots((n) => n - 1)}
              disabled={shots <= 0}
              aria-label="Bir shot azalt"
            >
              −
            </button>
            <span className="stepper-value" aria-live="polite">
              {shots}
            </span>
            <button
              type="button"
              className="stepper-button"
              onClick={() => setShots((n) => n + 1)}
              disabled={shots >= MAX_EXTRA_SHOTS}
              aria-label="Bir shot artır"
            >
              +
            </button>
          </div>
        </div>
      </section>

      {/* Kredi bilgisi */}
      <section className="credit-box">
        {!hasSubscription && (
          <>
            <strong>Aktif aboneliğin yok</strong>
            <p>Sipariş verebilmek için önce bir paket seçmelisin.</p>
          </>
        )}

        {outOfCredits && (
          <>
            <strong>Kahve hakkın bitti</strong>
            <p>
              Bu dönemki hakkın bitti, {formatDate(subscription.expires_at)} tarihinde yenilenecek. İstersen paketini
              yükseltebilirsin.
            </p>
          </>
        )}

        {hasSubscription && !outOfCredits && (
          <>
            <div className="credit-row">
              <span>{subscription.plan.name} paketi · Kalan kahve hakkın</span>
              <strong className="credit-number">{unlimited ? 'Sınırsız' : remaining}</strong>
            </div>
            {unlimited ? (
              <p className="credit-after">Paketin sınırsız, bu sipariş hakkından düşmez.</p>
            ) : creditsAfter === 0 ? (
              <p className="credit-after credit-after-warn">
                Bu senin son hakkın: bu sipariş sonrası <strong>0</strong> kredi kalacak.
              </p>
            ) : (
              <p className="credit-after">
                Bu sipariş sonrası <strong>{creditsAfter}</strong> kredi kalacak.
              </p>
            )}
          </>
        )}
      </section>

      {submitError && <div className="alert alert-error">{submitError}</div>}

      <button type="button" className="button button-block" disabled={!canOrder} onClick={handleConfirm}>
        {submitting ? 'Sipariş veriliyor…' : 'Siparişi Onayla'}
      </button>

      {(!hasSubscription || outOfCredits) && (
        <Link to="/abonelik" className="button button-block button-secondary">
          {hasSubscription ? 'Paketini yükselt' : 'Abonelik sayfasına git'}
        </Link>
      )}

      {!product.is_available && <p className="field-error">Bu ürün şu an satışta değil.</p>}
    </div>
  )
}
