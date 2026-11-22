"""Ürün kategorisi.

Veritabanında ürün kategorisi sütunu yok (şema migration'ı henüz kurulu değil), bu yüzden kategori ürün adından
türetilir. Sıra önemlidir: "Iced Latte" hem soğuk hem espresso bazlıdır, soğuk olan önce kontrol edildiği için
"Soğuk İçecekler"e düşer. Tanınmayan her isim "other" (Diğer) olur.
Kalıcı çözüm: products tablosuna category sütunu eklemek (migration kurulunca).
"""
from app.core.text import fold

_COLD = ("iced", "cold brew", "soguk", "buzlu", "frappe", "tonic")
_FILTER = ("filtre", "filter", "v60", "chemex", "aeropress")
_ESPRESSO = (
    "espresso", "americano", "cappuccino", "latte", "flat white", "mocha", "macchiato", "cortado", "ristretto", "lungo",
)


def category_for(name: str) -> str:
    """'espresso' | 'filter' | 'cold' | 'other'"""
    folded = fold(name)
    if any(word in folded for word in _COLD):
        return "cold"
    if any(word in folded for word in _FILTER):
        return "filter"
    if any(word in folded for word in _ESPRESSO):
        return "espresso"
    return "other"
