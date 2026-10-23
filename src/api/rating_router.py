# -*- coding: utf-8 -*-
"""
Router xử lý các API endpoint liên quan đến Đánh giá phim (Ratings):
- Gửi đánh giá sao cho phim: POST /api/ratings
- Lấy danh sách đánh giá của người dùng: GET /api/ratings
- Lấy đánh giá của người dùng cho một phim cụ thể: GET /api/ratings/{movie_id}
- Xóa đánh giá của người dùng cho một phim: DELETE /api/ratings/{movie_id}
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, Rating
from ..schemas.interaction import RatingCreate, RatingResponse
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/ratings", tags=["Đánh giá phim"])

@router.post("", response_model=RatingResponse, summary="Gửi đánh giá sao cho bộ phim")
def rate_movie(
    rating_in: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gửi hoặc cập nhật điểm đánh giá sao (từ 1.0 đến 10.0) cho phim:
    - Nếu đã từng đánh giá phim này: tự động cập nhật lại số điểm và thời gian
    - Nếu chưa đánh giá: tạo bản ghi đánh giá mới
    """
    now = datetime.now(timezone.utc)
    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == rating_in.movie_id
    ).first()
    
    if existing_rating:
        # Cập nhật đánh giá cũ
        existing_rating.score = rating_in.score
        existing_rating.updated_at = now
        if rating_in.comment is not None:
            existing_rating.comment = rating_in.comment
        if rating_in.movie_title:
            existing_rating.movie_title = rating_in.movie_title
        if rating_in.poster_url:
            existing_rating.poster_url = rating_in.poster_url
            
        db.commit()
        db.refresh(existing_rating)
        return existing_rating
        
    # Tạo đánh giá mới
    new_rating = Rating(
        user_id=current_user.id,
        movie_id=rating_in.movie_id,
        score=rating_in.score,
        comment=rating_in.comment,
        movie_title=rating_in.movie_title,
        poster_url=rating_in.poster_url,
        created_at=now,
        updated_at=now
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    
    return new_rating

@router.get("", response_model=List[RatingResponse], summary="Lấy danh sách các phim người dùng đã đánh giá")
def get_user_ratings(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy toàn bộ các bộ phim mà tài khoản hiện tại đã đánh giá sao."""
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id
    ).order_by(
        Rating.updated_at.desc()
    ).limit(limit).all()
    
    return ratings

@router.get("/{movie_id}", response_model=Optional[RatingResponse], summary="Lấy điểm đánh giá của tài khoản cho một phim cụ thể")
def get_single_movie_rating(
    movie_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kiểm tra xem người dùng hiện tại đã từng chấm điểm cho phim này chưa."""
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()
    
    return rating

@router.delete("/{movie_id}", status_code=status.HTTP_200_OK, summary="Xóa đánh giá của tài khoản cho một phim cụ thể")
def delete_single_rating(
    movie_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa đánh giá của người dùng cho một phim cụ thể (bảo vệ quyền riêng tư & reset gu gợi ý).
    Bảo vệ IDOR: Chỉ xóa bản ghi có user_id trùng khớp với current_user.id.
    """
    entry = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đánh giá của bạn cho bộ phim này."
        )
        
    db.delete(entry)
    db.commit()
    return {"message": "Đã xóa đánh giá thành công.", "movie_id": movie_id}

