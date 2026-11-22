import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { listMyOrders } from '../api/orders'
import StatusPill from '../components/StatusPill'
import { formatDateTime } from '../utils/format'
import { describeOptions } from '../utils/order'

const PAGE_SIZE = 20

export default function History() {
  const [state, setState] = useState({ items: [], loaded: false, error: '', hasMore: false })
  const [reloadKey, setReloadKey] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const [moreError, setMoreError] = useState('')

  // İlk sayfa: en yeni 20 sipariş (backend zaten en yeniden eskiye sıralı verir).
  useEffect(() => {
    let cancelled = false
    listMyOrders({ limit: PAGE_SIZE, offset: 0 })
      .then((items) => !cancelled && setState({ items, loaded: true, error: '', hasMore: items.length === PAGE_SIZE }))
      .catch((error) => {
        if (cancelled) return
        const message =
          error?.response?.status === 403
            ? 'Sipariş geçmişi yalnızca müşteri hesapları içindir.'
            : getErrorMessage(error)
        setState({ items: [], loaded: true, error: message, hasMore: false })
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  function retry() {
    setState((s) => ({ ...s, loaded: false, error: '' }))
    setReloadKey((k) => k + 1)
  }

  async function loadMore() {
    setLoadingMore(true)
    setMoreError('')
    try {
      const next = await listMyOrders({ limit: PAGE_SIZE, offset: state.items.length })
      setState((s) => ({ ...s, items: [...s.items, ...next], hasMore: next.length === PAGE_SIZE }))
    } catch (error) {
      setMoreError(getErrorMessage(error))
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div className="page-narrow">
      <h1>Sipariş geçmişi</h1>
      <p className="muted">Önceki siparişlerin, en yenisi üstte.</p>

      {!state.loaded && <p className="muted">Siparişler yükleniyor…</p>}

      {state.loaded && state.error && (
        <div className="alert alert-error">
          {state.error}{' '}
          <button type="button" className="link-button" onClick={retry}>
            Tekrar dene
          </button>
        </div>
      )}

      {state.loaded && !state.error && state.items.length === 0 && (
        <div className="empty-state">
          <p>Henüz hiç sipariş vermedin.</p>
          <Link to="/" className="button">
            Dükkânları keşfet
          </Link>
        </div>
      )}

      {state.items.length > 0 && (
        <ul className="history-list">
          {state.items.map((order) => (
            <li key={order.id}>
              <Link to={`/qr/${order.id}`} className="history-row">
                <span className="history-date">{formatDateTime(order.created_at)}</span>
                <span className="history-main">
                  <strong>{order.product.name}</strong>
                  <span className="muted">{order.shop.name}</span>
                  <span className="small muted">{describeOptions(order)}</span>
                </span>
                <StatusPill status={order.status} />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {moreError && <div className="alert alert-error">{moreError}</div>}

      {state.hasMore && (
        <button type="button" className="button button-block button-secondary" onClick={loadMore} disabled={loadingMore}>
          {loadingMore ? 'Yükleniyor…' : 'Daha eski siparişleri göster'}
        </button>
      )}
    </div>
  )
}
