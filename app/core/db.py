from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from collections.abc import Generator
from app.core.settings import settings

# 1. Create the sync engine
# Note: connect_args={"check_same_thread": False} is only required if you are using SQLite
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 2. Create the session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# 3. Create a dependency injector for your routes/endpoints
def get_db() -> Generator[Session, None, None]:
    """Dependency provider for database sessions. Automatically closes the session after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
