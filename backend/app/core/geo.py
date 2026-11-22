"""Konum hesapları (Haversine formülü)."""
import math

EARTH_RADIUS_KM = 6371.0088
KM_PER_DEGREE = EARTH_RADIUS_KM * math.pi / 180  # enlemde 1 derece ~ 111.2 km


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """İki koordinat arasındaki kuş uçuşu mesafe (km)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float | None, float | None]:
    """Yarıçapı içine alan kare: (min_lat, max_lat, min_lng, max_lng).
    Veritabanında indeksli hızlı ön eleme için kullanılır; kesin mesafe sonra Haversine ile hesaplanır.
    Kutu bilerek %1 geniş tutulur, böylece sınırdaki bir dükkân yanlışlıkla elenmez."""
    radius_km *= 1.01
    d_lat = radius_km / KM_PER_DEGREE
    cos_lat = math.cos(math.radians(lat))
    if abs(lat) > 89 or cos_lat < 1e-6:
        return lat - d_lat, lat + d_lat, None, None  # kutuplara çok yakın: boylam sınırı uygulanmaz
    d_lng = radius_km / (KM_PER_DEGREE * cos_lat)
    return lat - d_lat, lat + d_lat, lng - d_lng, lng + d_lng
