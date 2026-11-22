import { api, unwrap } from './client'

// Kayıt: numara yoksa hesap açar, ardından doğrulama kodu "gönderir".
export const requestRegisterOtp = (phone) =>
  api.post('/auth/register', { phone_number: phone }).then(unwrap)

// Giriş: yalnızca kayıtlı numaralara kod gönderir (kayıtsızsa USER_NOT_FOUND hatası).
export const requestLoginOtp = (phone) =>
  api.post('/auth/login', { phone_number: phone }).then(unwrap)

// Kodu doğrular. Dönen veri: { access_token, refresh_token, user }
export const verifyOtp = (phone, code) =>
  api.post('/auth/verify-otp', { phone_number: phone, code }).then(unwrap)

// Profil bilgisi (ad soyad vb.) kaydeder. Dönen veri: güncel kullanıcı.
export const updateProfile = (fields) => api.patch('/users/me', fields).then(unwrap)
