from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
from config import settings

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,        # Increase from default 5
    max_overflow=40,     # Allow up to 40 additional connections
    pool_timeout=30,     # Wait up to 30 seconds for a connection
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connections before using them
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    from models import Job  # noqa: F401 — ensures model is registered
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
