import { useEffect, useRef } from 'react'

// Ortada açılan pencere. Tarayıcının kendi <dialog> özelliğini kullanır:
// arka planı karartır, Esc ile kapanır, odağı pencerenin içinde tutar.
// busy=true iken (işlem sürerken) kapatılamaz.
export default function Modal({ title, onClose, busy = false, children }) {
  const ref = useRef(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog.open) dialog.showModal()
    return () => dialog.close()
  }, [])

  return (
    <dialog
      ref={ref}
      className="modal"
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault() // Esc tuşu: kapatmayı biz yönetiyoruz
        if (!busy) onClose()
      }}
      onClick={(event) => {
        if (event.target === ref.current && !busy) onClose() // karartılmış alana tıklama
      }}
    >
      <div className="modal-body">
        <div className="modal-head">
          <h2>{title}</h2>
          <button type="button" className="modal-close" onClick={onClose} disabled={busy} aria-label="Kapat">
            ×
          </button>
        </div>
        {children}
      </div>
    </dialog>
  )
}
