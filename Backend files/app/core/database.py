# SmartStore ERP — Database Connection
# Ye file SQLite database se connection banati hai
# SQLAlchemy = Python ka tool jo database se baat karta hai (ORM)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# Engine = database ka connection pipe
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite ke liye zaroori hai
)

# Session = ek conversation with database (data lo, do, update karo)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class — saare models (tables) isse inherit karenge
class Base(DeclarativeBase):
    pass


# Ye function har API call mein database session deta hai, kaam hone pe band karta hai
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
