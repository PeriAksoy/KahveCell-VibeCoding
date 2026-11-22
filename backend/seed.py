"""Örnek veri yükleyici (Ankara).

Çalıştırma (backend klasöründen):
    python seed.py            -> veri yoksa yükler, varsa dokunmadan çıkar
    python seed.py --reset    -> TÜM tabloları silip sıfırdan yükler
"""
import sys
from datetime import timedelta
from decimal import Decimal

from app.core.database import Base, SessionLocal, engine
from app.models import Plan, Product, Shop, Subscription, User
from app.models.enums import PlanType, SubscriptionStatus, UserRole
from app.models.user import utcnow

TEST_PHONE = "+905551234567"  # giriş: bu numara + OTP kodu 1234
ADMIN_PHONE = "+905550000000"

PLANS = [
    (PlanType.STARTER, "Starter", "89.99", 10, 0, False),
    (PlanType.PREMIUM, "Premium", "149.99", 20, 2, False),
    (PlanType.UNLIMITED, "Unlimited", "249.99", None, 5, True),  # None = sınırsız
]

# Koordinatlar semtlerin ana caddelerine yakın, yaklaşık değerlerdir (~100-200 m hassasiyet).
# Dükkân isimleri kurgusaldır.
SHOPS = [
    {
        "name": "Güvenpark Kahve",
        "address": "Kızılay, Atatürk Bulvarı, Çankaya/Ankara",
        "lat": 39.9208, "lng": 32.8541,
        "opens": "07:30", "closes": "23:00", "rating": 4.6,
        "menu": [
            ("Espresso", "Tek shot, yoğun", "95"),
            ("Americano", "Espresso ve sıcak su", "120"),
            ("Cappuccino", "Espresso, sütlü köpük", "140"),
            ("Latte", "Espresso, bol süt", "150"),
            ("Türk Kahvesi", "Közde, lokum ile", "90"),
        ],
    },
    {
        "name": "Tunalı Roastery",
        "address": "Tunalı Hilmi Caddesi, Çankaya/Ankara",
        "lat": 39.9066, "lng": 32.8587,
        "opens": "08:00", "closes": "22:30", "rating": 4.8,
        "menu": [
            ("Espresso", "Tek shot, yoğun", "100"),
            ("Flat White", "Çift shot, ince süt", "160"),
            ("Cappuccino", "Espresso, sütlü köpük", "145"),
            ("Filtre Kahve", "V60 demleme", "115"),
            ("Cold Brew", "12 saat soğuk demleme", "165"),
            ("Mocha", "Espresso, çikolata, süt", "170"),
        ],
    },
    {
        "name": "7. Cadde Kahve Evi",
        "address": "Bahçelievler 7. Cadde, Çankaya/Ankara",
        "lat": 39.9222, "lng": 32.8255,
        "opens": "09:00", "closes": "23:30", "rating": 4.4,
        "menu": [
            ("Espresso", "Tek shot, yoğun", "90"),
            ("Latte", "Espresso, bol süt", "140"),
            ("Türk Kahvesi", "Közde, lokum ile", "85"),
            ("Menengiç Kahvesi", "Sütlü, kremamsı", "110"),
            ("Sıcak Çikolata", "Bitter çikolata, süt", "130"),
        ],
    },
    {
        "name": "Çayyolu Bean",
        "address": "Çayyolu, Çankaya/Ankara",
        "lat": 39.8870, "lng": 32.6890,
        "opens": "08:00", "closes": "22:00", "rating": 4.3,
        "menu": [
            ("Espresso", "Tek shot, yoğun", "95"),
            ("Americano", "Espresso ve sıcak su", "115"),
            ("Cappuccino", "Espresso, sütlü köpük", "135"),
            ("Iced Latte", "Buzlu, espresso ve süt", "150"),
            ("Filtre Kahve", "Günün çekirdeği", "105"),
        ],
    },
    {
        "name": "Hamamönü Kahvesi",
        "address": "Hamamönü, Altındağ/Ankara",
        "lat": 39.9385, "lng": 32.8625,
        "opens": "10:00", "closes": "00:00", "rating": 4.7,
        "menu": [
            ("Türk Kahvesi", "Közde, lokum ile", "80"),
            ("Dibek Kahvesi", "Geleneksel, bol köpüklü", "95"),
            ("Espresso", "Tek shot, yoğun", "90"),
            ("Salep", "Tarçınlı, sıcak", "110"),
        ],
    },
]


def add_shop(db, owner: User, spec: dict) -> int:
    """Dükkânı ve menüsünü ekler, eklenen ürün sayısını döner."""
    shop = Shop(
        owner_id=owner.id, name=spec["name"], address=spec["address"],
        latitude=spec["lat"], longitude=spec["lng"],
        opens_at=spec["opens"], closes_at=spec["closes"], rating=spec["rating"],
    )
    db.add(shop)
    db.flush()
    for name, desc, price in spec["menu"]:
        db.add(Product(shop_id=shop.id, name=name, description=desc, base_price=Decimal(price)))
    return len(spec["menu"])


def main() -> None:
    reset = "--reset" in sys.argv
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Admin hesabı her seferinde kontrol edilir; yoksa eklenir (veri zaten yüklü olsa bile).
        if db.query(User).filter_by(phone_number=ADMIN_PHONE).first() is None:
            db.add(User(phone_number=ADMIN_PHONE, full_name="Sistem Admin", role=UserRole.ADMIN))
            db.commit()
            print(f"Admin hesabı eklendi: {ADMIN_PHONE}  (OTP: 1234)")

        if db.query(Plan).count() > 0:
            print("Veritabanında zaten veri var, hiçbir şey eklenmedi.")
            print("Sıfırdan yüklemek için: python seed.py --reset")
            return

        plans = {}
        for code, name, price, credits, guests, priority in PLANS:
            plan = Plan(
                code=code, name=name, monthly_price=Decimal(price),
                monthly_credits=credits, guest_passes=guests, has_priority=priority,
            )
            db.add(plan)
            plans[code] = plan

        owners = []
        for i, shop in enumerate(SHOPS, start=1):
            owner = User(
                phone_number=f"+90555999000{i}",
                full_name=f"{shop['name']} Sahibi",
                role=UserRole.SHOP_OWNER,
            )
            db.add(owner)
            owners.append(owner)

        customer = User(
            phone_number=TEST_PHONE,
            full_name="Test Kullanıcı",
            email="test@kahvecell.local",
            role=UserRole.CUSTOMER,
            preferences={"coffees": ["Latte", "Türk Kahvesi"], "allergens": []},
        )
        db.add(customer)
        db.flush()  # id'ler oluşsun

        now = utcnow()
        db.add(Subscription(
            user_id=customer.id,
            plan_id=plans[PlanType.STARTER].id,
            remaining_credits=10,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=now + timedelta(days=30),
        ))

        product_count = sum(add_shop(db, owner, spec) for owner, spec in zip(owners, SHOPS))

        db.commit()

    print(f"Yüklendi: {len(PLANS)} paket, {len(SHOPS)} dükkân, {product_count} ürün.")
    print(f"Test müşterisi : {TEST_PHONE}  (OTP: 1234)  -> Starter paketi, 10 kahve hakkı")
    print("Test dükkân sahibi: +905559990001 (Güvenpark Kahve)  (OTP: 1234)")


if __name__ == "__main__":
    main()
