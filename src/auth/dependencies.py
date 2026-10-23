"""
Module cung cấp các FastAPI Dependencies liên quan đến kiểm tra quyền và xác thực người dùng.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User
from .security import decode_access_token

# Sử dụng HTTPBearer cho chuẩn RESTful API header: Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency kiểm tra JWT Token và trích xuất thực thể User tương ứng.
    Bắt buộc phải đăng nhập (yêu cầu token hợp lệ).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
        
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if not username:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
        
    return user

