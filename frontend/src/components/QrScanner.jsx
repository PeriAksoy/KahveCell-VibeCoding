import jsQR from 'jsqr'
import { useEffect, useRef } from 'react'

const MAX_WIDTH = 1024 // çözümleme için kare en fazla bu genişliğe küçültülür (küçültme QR'ı okumayı zorlaştırır)
const SCAN_INTERVAL_MS = 150

function describeCameraError(error) {
  switch (error?.name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'Kamera izni verilmedi. Tarayıcının adres çubuğundan kameraya izin verip tekrar dene.'
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'Kamera bulunamadı.'
    case 'NotReadableError':
      return 'Kamera başka bir uygulama tarafından kullanılıyor olabilir.'
    default:
      return 'Kamera açılamadı.'
  }
}

// Kamerayı açar ve görüntüde QR kod arar. İlk QR bulununca onScan(metin) çağırır ve taramayı durdurur.
// Kamera açılamazsa onError(mesaj) çağrılır. Bileşen kapanınca kamera otomatik kapatılır.
export default function QrScanner({ onScan, onError }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  // Callback'lerin güncel halini tutar; böylece kamera, bileşen yeniden çizilince yeniden başlamaz.
  const callbacks = useRef({ onScan, onError })
  useEffect(() => {
    callbacks.current = { onScan, onError }
  })

  useEffect(() => {
    let stopped = false
    let stream = null
    let timer = null

    function tick() {
      if (stopped) return
      const video = videoRef.current
      const canvas = canvasRef.current
      if (video && video.readyState === video.HAVE_ENOUGH_DATA && video.videoWidth > 0) {
        const scale = Math.min(1, MAX_WIDTH / video.videoWidth)
        const width = Math.round(video.videoWidth * scale)
        const height = Math.round(video.videoHeight * scale)
        canvas.width = width
        canvas.height = height
        const context = canvas.getContext('2d', { willReadFrequently: true })
        context.drawImage(video, 0, 0, width, height)
        const frame = context.getImageData(0, 0, width, height)
        const code = jsQR(frame.data, width, height, { inversionAttempts: 'dontInvert' })
        if (code?.data) {
          stopped = true
          callbacks.current.onScan(code.data)
          return
        }
      }
      timer = setTimeout(tick, SCAN_INTERVAL_MS)
    }

    async function start() {
      try {
        if (!navigator.mediaDevices?.getUserMedia) throw new Error('unsupported')
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
        if (stopped) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        videoRef.current.srcObject = stream
        await videoRef.current.play()
        tick()
      } catch (error) {
        if (!stopped) callbacks.current.onError(describeCameraError(error))
      }
    }

    start()
    return () => {
      stopped = true
      clearTimeout(timer)
      stream?.getTracks().forEach((track) => track.stop())
    }
  }, [])

  return (
    <div className="scanner">
      <video ref={videoRef} className="scanner-video" muted playsInline />
      <div className="scanner-frame" aria-hidden="true" />
      <canvas ref={canvasRef} hidden />
    </div>
  )
}
