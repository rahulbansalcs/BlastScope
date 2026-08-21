from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from app.core.config import settings
class Base(DeclarativeBase):
    pass
engine=None
SessionLocal=None
def initialize_database():
    global engine,SessionLocal
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    engine=create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300
    )
    SessionLocal=sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    return engine
def get_session():
    global SessionLocal
    if SessionLocal is None:
        initialize_database()
    session=SessionLocal()
    try:
        yield session
    finally:
        session.close()