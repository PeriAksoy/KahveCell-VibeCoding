// Backend ile aynı kural: 0555 123 45 67, 5551234567, +905551234567 hepsi geçerli.
// Geçerliyse "+905551234567" biçimini, değilse null döner.
export function normalizePhone(raw) {
  const digits = raw.replace(/[\s\-()]/g, '').replace(/^\+/, '')
  if (!/^\d+$/.test(digits)) return null
  let local = digits
  if (digits.length === 12 && digits.startsWith('90')) local = digits.slice(2)
  else if (digits.length === 11 && digits.startsWith('0')) local = digits.slice(1)
  if (local.length !== 10 || !local.startsWith('5')) return null
  return `+90${local}`
}

// "+905551234567" -> "+90 555 123 45 67"
export function formatPhone(normalized) {
  const d = normalized.replace('+90', '')
  return `+90 ${d.slice(0, 3)} ${d.slice(3, 6)} ${d.slice(6, 8)} ${d.slice(8)}`
}
