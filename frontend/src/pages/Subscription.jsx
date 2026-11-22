import { useEffect, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { cancelSubscription, changePlan, getMySubscription, listPlans } from '../api/subscriptions'
import ConfirmModal from '../components/ConfirmModal'
import PaymentModal from '../components/PaymentModal'
import PlanCard from '../components/PlanCard'
import { formatDate, formatPrice } from '../utils/format'

const fetchAll = async () => {
  const [plans, subscription] = await Promise.all([listPlans(), getMySubscription()])
  return { plans, subscription }
}

const round2 = (n) => Math.round(n * 100) / 100

export default function Subscription() {
  const [data, setData] = useState({ loaded: false, plans: [], subscription: null, error: '' })
  const [reloadKey, setReloadKey] = useState(0)
  const [dialog, setDialog] = useState(null) // açık pencere: { type: 'pay' | 'downgrade' | 'cancel', ... }
  const [notice, setNotice] = useState(null) // üstteki bildirim: { type: 'success' | 'error', text }

  useEffect(() => {
    let cancelled = false
    fetchAll()
      .then((result) => !cancelled && setData({ loaded: true, ...result, error: '' }))
      .catch((error) => {
        if (cancelled) return
        const message =
          error?.response?.status === 403 ? 'Abonelik yalnızca müşteri hesapları içindir.' : getErrorMessage(error)
        setData({ loaded: true, plans: [], subscription: null, error: message })
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  // Bildirim 8 saniye sonra kendiliğinden kapanır.
  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(() => setNotice(null), 8000)
    return () => clearTimeout(timer)
  }, [notice])

  function retry() {
    setData((d) => ({ ...d, loaded: false, error: '' }))
    setReloadKey((k) => k + 1)
  }

  // Bir işlemden sonra sayfanın üst kısmını (aktif abonelik) ve paket kartlarını yeniler; yükleniyor ekranı göstermez.
  async function refresh() {
    try {
      setData({ loaded: true, ...(await fetchAll()), error: '' })
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) })
    }
  }

  function finish(text) {
    setDialog(null)
    setNotice({ type: 'success', text })
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return refresh()
  }

  const { plans, subscription } = data

  // Kartın butonu: abonelik yoksa "Satın Al"; varsa daha pahalı paket "Yükselt", ucuz paket "Düşür".
  function actionFor(plan) {
    if (!subscription) return { label: 'Satın Al', disabled: false }
    if (plan.code === subscription.plan.code) return { label: 'Mevcut paketin', disabled: true }
    const upgrade = Number(plan.monthly_price) > Number(subscription.plan.monthly_price)
    return { label: upgrade ? 'Yükselt' : 'Düşür', disabled: false }
  }

  function handleSelect(plan) {
    if (!subscription) {
      setDialog({ type: 'pay', mode: 'subscribe', plan, amount: Number(plan.monthly_price) })
      return
    }
    const difference = round2(Number(plan.monthly_price) - Number(subscription.plan.monthly_price))
    if (difference > 0) setDialog({ type: 'pay', mode: 'upgrade', plan, amount: difference })
    else setDialog({ type: 'downgrade', plan })
  }

  function handlePaid(result) {
    const { mode, plan } = dialog
    const { amount, transaction_id: transactionId } = result.payment
    const text =
      mode === 'upgrade'
        ? `Paketin ${plan.name} olarak yükseltildi. Fark ücreti ${formatPrice(amount)} tahsil edildi. İşlem no: ${transactionId}`
        : `${plan.name} paketine abone oldun! ${formatPrice(amount)} tahsil edildi. İşlem no: ${transactionId}`
    return finish(text)
  }

  const credits = subscription && !subscription.is_unlimited ? subscription.remaining_credits : null
  const creditPercent =
    credits !== null ? Math.max(0, Math.min(100, (credits / subscription.plan.monthly_credits) * 100)) : 100

  return (
    <div className="page-medium">
      <h1>Abonelik</h1>

      {notice && (
        <div className={`notice notice-${notice.type}`} role="status">
          <span>{notice.type === 'success' ? '✅ ' : '⚠️ '}{notice.text}</span>
          <button type="button" className="notice-close" onClick={() => setNotice(null)} aria-label="Bildirimi kapat">
            ×
          </button>
        </div>
      )}

      {!data.loaded && <p className="muted">Yükleniyor…</p>}

      {data.loaded && data.error && (
        <div className="alert alert-error">
          {data.error}{' '}
          <button type="button" className="link-button" onClick={retry}>
            Tekrar dene
          </button>
        </div>
      )}

      {data.loaded && !data.error && (
        <>
          {/* Üst kısım: aktif abonelik */}
          {subscription ? (
            <section className="sub-box">
              <div className="sub-box-head">
                <div>
                  <span className="muted small">Aktif aboneliğin</span>
                  <h2>{subscription.plan.name}</h2>
                </div>
                <button type="button" className="button button-secondary button-danger-outline" onClick={() => setDialog({ type: 'cancel' })}>
                  İptal Et
                </button>
              </div>

              <div className="sub-stats">
                <div>
                  <span className="muted small">Kalan kahve hakkı</span>
                  <strong className="sub-credits">{subscription.is_unlimited ? 'Sınırsız' : credits}</strong>
                  {credits !== null && (
                    <div className="meter" role="img" aria-label={`${credits} / ${subscription.plan.monthly_credits} hak kaldı`}>
                      <div className="meter-fill" style={{ width: `${creditPercent}%` }} />
                    </div>
                  )}
                </div>
                <div>
                  <span className="muted small">Bitiş tarihi</span>
                  <strong className="sub-date">{formatDate(subscription.expires_at)}</strong>
                  <span className="muted small">Dönem sonunda otomatik yenilenir.</span>
                </div>
              </div>
            </section>
          ) : (
            <section className="sub-box sub-box-empty">
              <strong>Aktif aboneliğiniz yok</strong>
              <p className="muted">Aşağıdan bir paket seçerek kahve hakkı kazanabilirsiniz.</p>
            </section>
          )}

          {/* Alt kısım: paketler */}
          <h2>Paketler</h2>
          <div className="plan-grid">
            {plans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                current={subscription?.plan.code === plan.code}
                action={actionFor(plan)}
                onSelect={handleSelect}
              />
            ))}
          </div>
        </>
      )}

      {/* Pencereler */}
      {dialog?.type === 'pay' && (
        <PaymentModal
          plan={dialog.plan}
          mode={dialog.mode}
          amount={dialog.amount}
          onClose={() => setDialog(null)}
          onSuccess={handlePaid}
        />
      )}

      {dialog?.type === 'downgrade' && (
        <ConfirmModal
          title={`${dialog.plan.name} paketine geç`}
          message={`Paketin ${dialog.plan.name} olarak değiştirilecek. Değişiklik hemen geçerli olur, ücret iadesi yapılmaz ve kalan hakkın yeni paketin aylık hakkını geçemez.`}
          confirmLabel="Paketi değiştir"
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await changePlan(dialog.plan.code)
            await finish(`Paketin ${dialog.plan.name} olarak değiştirildi.`)
          }}
        />
      )}

      {dialog?.type === 'cancel' && (
        <ConfirmModal
          title="Aboneliği iptal et"
          message="Aboneliğin hemen iptal edilir. Kalan kahve haklarını kullanamazsın ve ücret iadesi yapılmaz. Emin misin?"
          confirmLabel="Aboneliği iptal et"
          danger
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await cancelSubscription()
            await finish('Aboneliğin iptal edildi.')
          }}
        />
      )}
    </div>
  )
}
