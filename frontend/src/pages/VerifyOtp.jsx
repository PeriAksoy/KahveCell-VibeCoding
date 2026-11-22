import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { requestLoginOtp, requestRegisterOtp, updateProfile, verifyOtp } from '../api/auth'
import { getErrorMessage } from '../api/client'
import { useAuthStore } from '../store/authStore'
import { formatPhone } from '../utils/phone'
import { homeFor } from '../utils/roles'

const TEST_CODE = '1234' // simülasyon: SMS gönderilmez, kod her zaman bu

export default function VerifyOtp() {
  const navigate = useNavigate()
  const location = useLocation()
  const { setSession, setUser } = useAuthStore()
  const { mode, phone, fullName, from, notice } = location.state ?? {}

  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)

  // Bu sayfaya doğrudan adresle gelindiyse (telefon bilgisi yoksa) giriş sayfasına dön.
  if (!phone) return <Navigate to="/giris" replace />

  async function handleSubmit(event) {
    event.preventDefault()
    if (code.length !== 4) {
      setError('Lütfen 4 haneli kodu girin.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const session = await verifyOtp(phone, code)
      setSession(session)
      // Yeni kayıtta, formda yazılan ad soyadı profile kaydet.
      if (mode === 'register' && fullName && !session.user.profile_complete) {
        try {
          setUser(await updateProfile({ full_name: fullName }))
        } catch {
          // Ad kaydedilemese de giriş başarılı; profil sonra tamamlanabilir.
        }
      }
      navigate(from ?? homeFor(session.user), { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
      setLoading(false)
    }
  }

  async function handleResend() {
    setError('')
    setInfo('')
    try {
      await (mode === 'register' ? requestRegisterOtp(phone) : requestLoginOtp(phone))
      setInfo('Kod tekrar gönderildi.')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <>
      <h1>Kodu gir</h1>
      <p className="auth-subtitle">
        <strong>{formatPhone(phone)}</strong> numarasına gelen 4 haneli kodu gir.
      </p>

      {notice && <div className="alert alert-info">{notice}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="code" className="visually-hidden">
            Doğrulama kodu
          </label>
          <input
            id="code"
            className="code-input"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            maxLength={4}
            placeholder="••••"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
          />
        </div>

        <div className="test-note">
          <span>
            🧪 Test modu: kod her zaman <strong>{TEST_CODE}</strong>
          </span>
          <button type="button" className="link-button" onClick={() => setCode(TEST_CODE)}>
            Doldur
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {info && <div className="alert alert-info">{info}</div>}

        <button type="submit" className="button button-block" disabled={loading}>
          {loading ? 'Doğrulanıyor…' : 'Doğrula ve devam et'}
        </button>
      </form>

      <p className="auth-footer">
        <button type="button" className="link-button" onClick={handleResend}>
          Kodu tekrar gönder
        </button>
        {' · '}
        <Link to={mode === 'register' ? '/kayit' : '/giris'} state={{ phone, from }}>
          Numarayı değiştir
        </Link>
      </p>
    </>
  )
}
