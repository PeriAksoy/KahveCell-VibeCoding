import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    SHOP_OWNER = "SHOP_OWNER"
    ADMIN = "ADMIN"


class PlanType(str, enum.Enum):
    STARTER = "STARTER"
    PREMIUM = "PREMIUM"
    UNLIMITED = "UNLIMITED"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class CupSize(str, enum.Enum):
    S = "S"
    M = "M"
    L = "L"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"      # müşteri verdi, dükkân henüz görmedi
    ACCEPTED = "ACCEPTED"    # dükkân kabul etti
    PREPARING = "PREPARING"  # hazırlanıyor
    READY = "READY"          # hazır, teslim bekliyor
    COMPLETED = "COMPLETED"  # QR okutuldu, teslim edildi
    CANCELLED = "CANCELLED"


# Sipariş durum makinesi: bir durumdan hangi durumlara geçilebilir.
ORDER_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


STATUS_LABELS = {
    OrderStatus.PENDING: "Onay bekliyor",
    OrderStatus.ACCEPTED: "Kabul edildi",
    OrderStatus.PREPARING: "Hazırlanıyor",
    OrderStatus.READY: "Hazır",
    OrderStatus.COMPLETED: "Teslim edildi",
    OrderStatus.CANCELLED: "İptal edildi",
}

# Dükkânın "kuyruk" ekranında gördüğü, henüz bitmemiş siparişler.
ACTIVE_ORDER_STATUSES = (OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY)


class MilkType(str, enum.Enum):
    WHOLE = "whole"  # tam yağlı
    SKIM = "skim"  # az yağlı
    LACTOSE_FREE = "lactose_free"  # laktozsuz
    OAT = "oat"  # yulaf
    ALMOND = "almond"  # badem
    SOY = "soy"  # soya
