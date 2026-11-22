// Arama için metni sadeleştirir: büyük/küçük harf ve Türkçe karakter farkını yok sayar.
// 'KIZILAY', 'Kızılay' ve 'kizilay' aynı sonucu verir (backend'deki fold ile aynı mantık).
export function fold(text) {
  return text
    .replaceAll('İ', 'i')
    .replaceAll('I', 'ı')
    .toLowerCase()
    .replace(/[ışğüöç]/g, (c) => ({ ı: 'i', ş: 's', ğ: 'g', ü: 'u', ö: 'o', ç: 'c' })[c])
}
