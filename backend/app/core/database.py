from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQL echo is controlled separately from DEBUG so that keeping DEBUG=true during
# development does not flood stdout with every SQL statement (a real slowdown on
# list/detail endpoints that used to emit dozens of queries per request).
engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
