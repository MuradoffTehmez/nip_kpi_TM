from contextlib import contextmanager

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import settings


KPI_DB_URL = settings.get_db_url
Base = declarative_base()
engine = create_engine(url=KPI_DB_URL)


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()