from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite + FastAPI için gerekli
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _):
    # SQLite varsayılanda foreign key kurallarını UYGULAMAZ; burada açıyoruz.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Her istek için bir veritabanı oturumu açar, iş bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
