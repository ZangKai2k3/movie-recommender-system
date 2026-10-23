"""
Định nghĩa các Pydantic Schemas phục vụ Lịch sử xem phim và Đánh giá (Rating).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# --- Lịch sử xem phim ---
class HistoryCreate(BaseModel):
    """Schema khi gửi yêu cầu lưu lịch sử xem phim."""
    movie_id: str = Field(..., max_length=50, description="Mã phim IMDb (ví dụ 'tt0816692')")
    movie_title: Optional[str] = Field(None, max_length=255, description="Tên phim")
    poster_url: Optional[str] = Field(None, max_length=500, description="Đường dẫn ảnh bìa poster")

class HistoryResponse(BaseModel):
    """Schema trả về thông tin lịch sử xem phim."""
    id: int
    movie_id: str
    movie_title: Optional[str]
    poster_url: Optional[str]
    watched_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Đánh giá phim ---
class RatingCreate(BaseModel):
    """Schema gửi đánh giá sao cho bộ phim."""
    movie_id: str = Field(..., description="Mã phim IMDb")
    score: float = Field(..., ge=1.0, le=10.0, description="Điểm đánh giá từ 1.0 đến 10.0")
    movie_title: Optional[str] = Field(None, description="Tên phim")
    poster_url: Optional[str] = Field(None, description="Link poster")
    comment: Optional[str] = Field(None, max_length=500, description="Bình luận ngắn")

class RatingResponse(BaseModel):
    """Schema trả về thông tin đánh giá phim."""
    id: int
    movie_id: str
    score: float
    movie_title: Optional[str]
    poster_url: Optional[str]
    comment: Optional[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

