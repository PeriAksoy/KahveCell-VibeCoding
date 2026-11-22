import { useState } from 'react'
import { getErrorMessage } from '../api/client'
import Modal from './Modal'

// "Emin misin?" penceresi (abonelik iptali, paket düşürme). onConfirm bir işlem yapar;
// hata fırlatırsa pencere açık kalır ve hatayı gösterir.
export default function ConfirmModal({ title, message, confirmLabel, danger = false, onConfirm, onClose }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleConfirm() {
    setBusy(true)
    setError('')
    try {
      await onConfirm()
    } catch (err) {
      setError(getErrorMessage(err))
      setBusy(false)
    }
  }

  return (
    <Modal title={title} onClose={onClose} busy={busy}>
      <p>{message}</p>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="modal-actions">
        <button type="button" className="button button-secondary" onClick={onClose} disabled={busy}>
          Vazgeç
        </button>
        <button type="button" className={`button ${danger ? 'button-danger' : ''}`} onClick={handleConfirm} disabled={busy}>
          {busy ? 'İşleniyor…' : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
