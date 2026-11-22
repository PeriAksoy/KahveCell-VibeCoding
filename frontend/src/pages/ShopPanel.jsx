import { useEffect, useMemo, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { listShopOrders, updateOrderStatus } from '../api/orders'
import PanelOrderCard from '../components/PanelOrderCard'
import ScanModal from '../components/ScanModal'
import { ORDER_STATUS, PANEL_TABS } from '../constants/orderStatus'

const POLL_MS = 5000 // liste kaç milisaniyede bir yenilenir

export default function ShopPanel() {
  const [state, setState] = useState({ orders: [], loaded: false, error: '', updatedAt: null })
  const [refreshKey, setRefreshKey] = useState(0) // artınca liste hemen yenilenir
  const [tab, setTab] = useState(PANEL_TABS[0].status)
  const [busyId, setBusyId] = useState(null)
  const [scanning, setScanning] = useState(null) // QR okutulan sipariş
  const [notice, setNotice] = useState(null)

  // Listeyi birkaç saniyede bir yeniler. (Her istek bitince bir sonraki planlanır, istekler üst üste binmez.)
  useEffect(() => {
    let cancelled = false
    let timer

    async function poll() {
      try {
        const orders = await listShopOrders()
        if (cancelled) return
        setState({ orders, loaded: true, error: '', updatedAt: Date.now() })
      } catch (error) {
        if (cancelled) return
        const message =
          error?.response?.status === 403 ? 'Bu sayfa yalnızca dükkân sahipleri içindir.' : getErrorMessage(error)
        // Geçici hata: eldeki listeyi koru, yalnızca uyarı göster.
        setState((s) => ({ ...s, loaded: true, error: message }))
      }
      timer = setTimeout(poll, POLL_MS)
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [refreshKey])

  // Bildirim 6 saniye sonra kapanır.
  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(() => setNotice(null), 6000)
    return () => clearTimeout(timer)
  }, [notice])

  // Siparişleri duruma göre sekmelere ayır (sıra backend'den geldiği gibi: öncelikli önde, sonra en eski).
  const byStatus = useMemo(() => {
    const groups = Object.fromEntries(PANEL_TABS.map((t) => [t.status, []]))
    for (const order of state.orders) groups[order.status]?.push(order)
    return groups
  }, [state.orders])

  const activeTab = PANEL_TABS.find((t) => t.status === tab)
  const visible = byStatus[tab]

  async function handleAction(order) {
    if (activeTab.action.scan) {
      setScanning(order)
      return
    }
    setBusyId(order.id)
    try {
      const next = activeTab.action.next
      await updateOrderStatus(order.id, next)
      setNotice({ type: 'success', text: `${order.product.name} · ${order.customer_name}: ${ORDER_STATUS[next].label}` })
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) })
    } finally {
      setBusyId(null)
      setRefreshKey((k) => k + 1) // sonuç ne olursa olsun güncel listeyi hemen çek
    }
  }

  function handleDelivered(order) {
    setScanning(null)
    setNotice({ type: 'success', text: `${order.product.name} · ${order.customer_name} teslim edildi ✓` })
    setRefreshKey((k) => k + 1)
  }

  return (
    <div className="page-medium">
      <h1>Sipariş paneli</h1>
      <p className="muted small">
        {state.updatedAt
          ? `Son güncelleme: ${new Date(state.updatedAt).toLocaleTimeString('tr-TR')} · liste ${POLL_MS / 1000} saniyede bir kendiliğinden yenilenir`
          : 'Siparişler yükleniyor…'}
      </p>

      {notice && (
        <div className={`notice notice-${notice.type}`} role="status">
          <span>{notice.type === 'success' ? '✅ ' : '⚠️ '}{notice.text}</span>
          <button type="button" className="notice-close" onClick={() => setNotice(null)} aria-label="Bildirimi kapat">
            ×
          </button>
        </div>
      )}

      {state.error && (
        <div className="alert alert-error">
          {state.error}
          {state.orders.length > 0 && ' Eldeki liste gösteriliyor, yeniden deneniyor…'}
        </div>
      )}

      <div className="panel-tabs" role="tablist" aria-label="Sipariş durumları">
        {PANEL_TABS.map((t) => (
          <button
            key={t.status}
            type="button"
            role="tab"
            aria-selected={tab === t.status}
            className={`panel-tab ${tab === t.status ? 'panel-tab-active' : ''}`}
            onClick={() => setTab(t.status)}
          >
            {t.label}
            <span className={`panel-count ${byStatus[t.status].length > 0 ? 'panel-count-on' : ''}`}>
              {byStatus[t.status].length}
            </span>
          </button>
        ))}
      </div>

      {!state.loaded && <p className="muted">Yükleniyor…</p>}

      {state.loaded && visible.length === 0 && !state.error && <p className="empty-state">{activeTab.empty}</p>}

      <div className="panel-grid" role="tabpanel">
        {visible.map((order) => (
          <PanelOrderCard
            key={order.id}
            order={order}
            action={activeTab.action}
            busy={busyId === order.id}
            onAction={handleAction}
          />
        ))}
      </div>

      {scanning && <ScanModal order={scanning} onClose={() => setScanning(null)} onDelivered={handleDelivered} />}
    </div>
  )
}
