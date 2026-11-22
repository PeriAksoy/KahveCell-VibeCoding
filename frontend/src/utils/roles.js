// Giriş yapan kullanıcının ilk gideceği sayfa: dükkân sahibi panele, diğerleri ana sayfaya.
export const homeFor = (user) => (user?.role === 'SHOP_OWNER' ? '/panel' : '/')
