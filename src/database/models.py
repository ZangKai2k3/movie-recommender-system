"""
Định nghĩa các bảng Cơ sở dữ liệu (ORM Models):
1. User: Lưu thông tin tài khoản người dùng (username, email, hashed_password)
2. WatchHistory: Lưu lịch sử xem phim của người dùng
3. Rating: Lưu điểm đánh giá (sao) của người dùng cho từng bộ phim
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .connection import Base

def utc_now():
    """Hàm trả về thời gian UTC có nhận biết múi giờ (timezone-aware)."""
    return datetime.now(timezone.utc)

class User(Base):
    """Bảng người dùng hệ thống."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Quan hệ 1-N với lịch sử xem và đánh giá
    history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan", order_by="desc(WatchHistory.watched_at)")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan", order_by="desc(Rating.updated_at)")


class WatchHistory(Base):
    """Bảng lưu lịch sử xem phim của người dùng."""
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(String(20), nullable=False, index=True)       # Ví dụ: 'tt0816692'
    movie_title = Column(String(255), nullable=True)                # Lưu kèm tên phim để truy xuất nhanh
    poster_url = Column(String(500), nullable=True)                 # Lưu link poster hiển thị
    watched_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    user = relationship("User", back_populates="history")


class Rating(Base):
    """Bảng lưu đánh giá (sao) của người dùng cho phim."""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(String(20), nullable=False, index=True)       # Mã phim IMDb
    movie_title = Column(String(255), nullable=True)
    poster_url = Column(String(500), nullable=True)
    score = Column(Float, nullable=False)                           # Thang điểm (ví dụ 1.0 đến 10.0 hoặc 1.0 đến 5.0)
    comment = Column(String(500), nullable=True)                    # Lời bình / review ngắn (tùy chọn)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Ràng buộc duy nhất: Mỗi người dùng chỉ đánh giá 1 phim 1 lần (nếu đánh giá lại sẽ cập nhật điểm)
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )

    user = relationship("User", back_populates="ratings")

