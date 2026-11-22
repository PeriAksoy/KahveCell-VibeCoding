import { useState } from 'react'
import { getErrorMessage } from '../api/client'
import { updateOrderStatus, verifyQr } from '../api/orders'
import { parseQrContent } from '../utils/qr'
import { describeOptions } from '../utils/order'
import Modal from './Modal'
import QrScanner from './QrScanner'

// "QR Okut" penceresi. Akış: kamera QR'ı okur → sunucu "gerçek mi" diye doğrular → dükkân "Teslim Et" der.
// phase: scanning (kamera açık) | checking (doğrulanıyor) | verified (gerçek) | failed (sorun var) | delivering
export default function ScanModal({ order, onClose, onDelivered }) {
  const [phase, setPhase] = useState('scanning')
  const [scanKey, setScanKey] = useState(0) // değişince kamera yeniden başlar
  const [cameraError, setCameraError] = useState('')
  const [problem, setProblem] = useState('')
  const [verified, setVerified] = useState(null) // { payload, result }
  const [manual, setManual] = useState('')

  // Okunan (veya elle yapıştırılan) QR metnini doğrular.
  async function handleContent(text) {
    setPhase('checking')
    setProblem('')
    try {
      const payload = parseQrContent(text)
      const result = await verifyQr(payload) // sahteyse backend hata verir
      if (payload.order_id.toLowerCase() !== order.id.toLowerCase()) {
        setProblem(
          `QR kod gerçek ama bu siparişe ait değil. Okutulan: ${result.order.product.name} · ${result.order.customer_name}. Doğru müşterinin QR kodunu okutun.`,
        )
        setPhase('failed')
      } else if (!result.can_deliver) {
        setProblem(result.message)
        setPhase('failed')
      } else {
        setVerified({ payload, result })
        setPhase('verified')
      }
    } catch (error) {
      setProblem(error?.response ? getErrorMessage(error) : error.message)
      setPhase('failed')
    }
  }

  async function handleDeliver() {
    setPhase('delivering')
    try {
      await updateOrderStatus(order.id, 'COMPLETED', verified.payload)
      onDelivered(order)
    } catch (error) {
      setProblem(getErrorMessage(error))
      setPhase('failed')
    }
  }

  function retry() {
    setProblem('')
    setVerified(null)
    setCameraError('')
    setScanKey((k) => k + 1)
    setPhase('scanning')
  }

  const busy = phase === 'checking' || phase === 'delivering'

  return (
    <Modal title="QR kodu okut" onClose={onClose} busy={busy}>
      <p className="scan-target">
        <strong>{order.product.name}</strong> · {order.customer_name}
        <br />
        <span className="muted small">{describeOptions(order)}</span>
      </p>

      {phase === 'scanning' && (
        <>
          {cameraError ? (
            <div className="alert alert-error">{cameraError}</div>
          ) : (
            <>
              <QrScanner key={scanKey} onScan={handleContent} onError={setCameraError} />
              <p className="muted small scan-hint">Müşterinin telefonundaki QR kodu kameraya göster.</p>
            </>
          )}

          <details className="scan-manual" open={Boolean(cameraError)}>
            <summary>Kamera yok mu? QR içeriğini elle yapıştır</summary>
            <textarea
              value={manual}
              onChange={(e) => setManual(e.target.value)}
              rows={4}
              placeholder='{"order_id":"…","user_id":"…","shop_id":"…","created_at":"…","signature":"…"}'
            />
            <button type="button" className="button" disabled={!manual.trim()} onClick={() => handleContent(manual)}>
              Doğrula
            </button>
          </details>
        </>
      )}

      {phase === 'checking' && <p className="muted">QR kod doğrulanıyor…</p>}

      {phase === 'verified' && (
        <>
          <div className="scan-ok">
            <strong>✓ QR kod gerçek</strong>
            <p>{verified.result.message}</p>
          </div>
          <div className="modal-actions">
            <button type="button" className="button button-secondary" onClick={onClose}>
              Vazgeç
            </button>
            <button type="button" className="button" onClick={handleDeliver}>
              Teslim Et
            </button>
          </div>
        </>
      )}

      {phase === 'delivering' && <p className="muted">Teslim ediliyor…</p>}

      {phase === 'failed' && (
        <>
          <div className="alert alert-error">
            <strong>⚠️ {problem}</strong>
          </div>
          <div className="modal-actions">
            <button type="button" className="button button-secondary" onClick={onClose}>
              Kapat
            </button>
            <button type="button" className="button" onClick={retry}>
              Tekrar tara
            </button>
          </div>
        </>
      )}
    </Modal>
  )
}
