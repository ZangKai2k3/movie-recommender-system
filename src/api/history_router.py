# -*- coding: utf-8 -*-
"""
Router xử lý các API endpoint liên quan đến Lịch sử xem phim (Watch History):
- Lưu lại lịch sử khi người dùng xem một bộ phim: POST /api/history
- Lấy danh sách phim người dùng đã xem gần đây: GET /api/history
- Xóa một phim khỏi lịch sử xem: DELETE /api/history/{movie_id}
- Xóa toàn bộ lịch sử xem của người dùng: DELETE /api/history
"""

from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, WatchHistory
from ..schemas.interaction import HistoryCreate, HistoryResponse
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/history", tags=["Lịch sử xem phim"])

@router.post("", response_model=HistoryResponse, status_code=status.HTTP_201_CREATED, summary="Lưu lịch sử khi người dùng xem một bộ phim")
def add_to_history(
    item: HistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ghi nhận một lượt xem phim vào bảng watch_history của tài khoản hiện tại.
    Nếu phim đã có trong lịch sử xem gần đây thì cập nhật lại mốc thời gian watched_at mới nhất.
    """
    now = datetime.now(timezone.utc)
    # Kiểm tra xem phim này đã từng được user xem chưa
    existing_entry = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id,
        WatchHistory.movie_id == item.movie_id
    ).first()
    
    if existing_entry:
        # Cập nhật thời gian xem mới nhất
        existing_entry.watched_at = now
        if item.movie_title:
            existing_entry.movie_title = item.movie_title
        if item.poster_url:
            existing_entry.poster_url = item.poster_url
        db.commit()
        db.refresh(existing_entry)
        return existing_entry
        
    # Tạo bản ghi mới cho người dùng hiện tại
    new_history = WatchHistory(
        user_id=current_user.id,
        movie_id=item.movie_id,
        movie_title=item.movie_title,
        poster_url=item.poster_url,
        watched_at=now
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    
    return new_history

@router.get("", response_model=List[HistoryResponse], summary="Lấy danh sách phim người dùng đã xem gần đây")
def get_user_history(
    limit: int = Query(20, ge=1, le=100, description="Số lượng bản ghi tối đa muốn lấy"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Truy vấn danh sách các bộ phim mà tài khoản hiện tại đã xem,
    sắp xếp theo thời gian xem gần đây nhất (watched_at giảm dần).
    """
    history_records = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id
    ).order_by(
        WatchHistory.watched_at.desc()
    ).limit(limit).all()
    
    return history_records

@router.delete("/{movie_id}", status_code=status.HTTP_200_OK, summary="Xóa một bộ phim khỏi lịch sử xem")
def delete_single_history(
    movie_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa một bản ghi phim cụ thể khỏi lịch sử xem của người dùng hiện tại.
    Bảo vệ IDOR: Chỉ xóa bản ghi thuộc quyền sở hữu của current_user.id.
    """
    entry = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id,
        WatchHistory.movie_id == movie_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bộ phim này trong lịch sử xem của bạn."
        )
        
    db.delete(entry)
    db.commit()
    return {"message": "Đã xóa phim khỏi lịch sử xem thành công.", "movie_id": movie_id}

@router.delete("", status_code=status.HTTP_200_OK, summary="Xóa toàn bộ lịch sử xem của người dùng")
def clear_all_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa toàn bộ danh sách lịch sử xem phim của người dùng hiện tại (bảo vệ quyền riêng tư).
    Bảo vệ IDOR: Chỉ xóa các bản ghi có user_id trùng với current_user.id.
    """
    deleted_count = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id
    ).delete(synchronize_session=False)
    
    db.commit()
    return {"message": f"Đã xóa toàn bộ {deleted_count} bộ phim khỏi lịch sử xem của bạn.", "deleted_count": deleted_count}

