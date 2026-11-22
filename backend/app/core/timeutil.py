from datetime import datetime, time, timedelta, timezone

# Türkiye 2016'dan beri tüm yıl UTC+3 kullanıyor (yaz/kış saati yok), sabit dilim yeterli.
TURKEY_TZ = timezone(timedelta(hours=3))


def as_utc(value: datetime) -> datetime:
    """SQLite saat dilimini saklamaz, okuyunca tarih 'naive' gelir. Burada UTC olarak kabul ediyoruz."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def turkey_now() -> datetime:
    return datetime.now(TURKEY_TZ)


def is_open_at(opens_at: str, closes_at: str, now: time) -> bool:
    """Çalışma saatleri 'HH:MM'. Gece yarısını aşan saatleri (18:00-02:00) ve '00:00' kapanışı da destekler.
    Açılış ve kapanış aynıysa 7/24 açık sayılır."""
    opens, closes = time.fromisoformat(opens_at), time.fromisoformat(closes_at)
    if opens == closes:
        return True
    if opens < closes:
        return opens <= now < closes
    return now >= opens or now < closes
