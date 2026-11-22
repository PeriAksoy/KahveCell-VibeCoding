import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { requestRegisterOtp } from '../api/auth'
import { getErrorMessage } from '../api/client'
import { normalizePhone } from '../utils/phone'

export default function Register() {
  const navigate = useNavigate()
  const location = useLocation()
  const [phone, setPhone] = useState(location.state?.phone ?? '')
  const [fullName, setFullName] = useState('')
  const [errors, setErrors] = useState({})
  const [submitError, setSubmitError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const normalized = normalizePhone(phone)
    const name = fullName.trim()
    const next = {}
    if (!normalized) next.phone = 'Geçerli bir cep telefonu numarası girin (örn. 555 123 45 67).'
    if (name.length < 2) next.fullName = 'Ad soyad en az 2 karakter olmalı.'
    setErrors(next)
    setSubmitError('')
    if (Object.keys(next).length > 0) return

    setLoading(true)
    try {
      const result = await requestRegisterOtp(normalized)
      navigate('/dogrula', {
        state: {
          mode: 'register',
          phone: normalized,
          fullName: name,
          from: location.state?.from,
          notice: result.is_new_user ? '' : 'Bu numara zaten kayıtlı, giriş yapıyoruz.',
        },
      })
    } catch (error) {
      setSubmitError(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1>Hesap oluştur</h1>
      <p className="auth-subtitle">Telefon numaranla birkaç saniyede kayıt ol.</p>

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="fullName">Ad soyad</label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            placeholder="Ayşe Yılmaz"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          {errors.fullName && <p className="field-error">{errors.fullName}</p>}
        </div>

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
          {errors.phone && <p className="field-error">{errors.phone}</p>}
        </div>

        {submitError && <div className="alert alert-error">{submitError}</div>}

        <button type="submit" className="button button-block" disabled={loading}>
          {loading ? 'Kod gönderiliyor…' : 'Devam et'}
        </button>
      </form>

      <p className="auth-footer">
        Zaten hesabın var mı? <Link to="/giris" state={location.state}>Giriş yap</Link>
      </p>
    </>
  )
}
