import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { requestLoginOtp } from '../api/auth'
import { getErrorMessage } from '../api/client'
import { normalizePhone } from '../utils/phone'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [phone, setPhone] = useState('')
  const [phoneError, setPhoneError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [notRegistered, setNotRegistered] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const normalized = normalizePhone(phone)
    setSubmitError('')
    setNotRegistered(false)
    if (!normalized) {
      setPhoneError('Geçerli bir cep telefonu numarası girin (örn. 555 123 45 67).')
      return
    }
    setPhoneError('')

    setLoading(true)
    try {
      await requestLoginOtp(normalized)
      navigate('/dogrula', {
        state: { mode: 'login', phone: normalized, from: location.state?.from },
      })
    } catch (error) {
      setSubmitError(getErrorMessage(error))
      setNotRegistered(error?.response?.data?.error?.code === 'USER_NOT_FOUND')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1>Tekrar hoş geldin</h1>
      <p className="auth-subtitle">Telefon numaranı gir, sana bir doğrulama kodu gönderelim.</p>

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="phone">Telefon numarası</label>
          <input
            id="phone"
            type="tel"
            autoComplete="tel"
            placeholder="555 123 45 67"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          {phoneError && <p className="field-error">{phoneError}</p>}
        </div>

        {submitError && (
          <div className="alert alert-error">
            {submitError}
            {notRegistered && (
              <>
                {' '}
                <Link to="/kayit" state={{ phone, from: location.state?.from }}>
                  Kayıt ol
                </Link>
              </>
            )}
          </div>
        )}

        <button type="submit" className="button button-block" disabled={loading}>
          {loading ? 'Kod gönderiliyor…' : 'Devam et'}
        </button>
      </form>

      <p className="auth-footer">
        Hesabın yok mu? <Link to="/kayit" state={location.state}>Kayıt ol</Link>
      </p>
    </>
  )
}
