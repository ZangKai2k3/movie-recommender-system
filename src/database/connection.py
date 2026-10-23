"""
Module kết nối Cơ sở dữ liệu SQLite thông qua SQLAlchemy ORM.
Cung cấp Engine, SessionLocal, Base và Dependency get_db().
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import DATABASE_URL

# Cấu hình engine kết nối cơ sở dữ liệu
# check_same_thread=False chỉ cần cho SQLite khi chạy trong tiến trình đa luồng của FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency cung cấp Database Session cho từng request và tự động đóng sau khi xử lý xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

