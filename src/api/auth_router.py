"""
Router xử lý các API endpoint liên quan đến Xác thực (Auth):
- Đăng ký tài khoản mới: POST /api/auth/register
- Đăng nhập sinh JWT Token thực tế: POST /api/auth/login
- Lấy thông tin tài khoản hiện tại: GET /api/auth/me
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database.connection import get_db
from ..database.models import User
from ..schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from ..auth.security import hash_password, verify_password, create_access_token
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Xác thực & Tài khoản"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản người dùng mới")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Tạo tài khoản mới trong cơ sở dữ liệu SQLite:
    - Kiểm tra tính duy nhất của username và email
    - Mã hóa mật khẩu bảo mật bằng bcrypt
    - Lưu vào bảng users
    """
    # 1. Kiểm tra xem username hoặc email đã tồn tại chưa
    existing_user = db.query(User).filter(
        or_(User.username == user_in.username, User.email == user_in.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Địa chỉ Email này đã được đăng ký tài khoản."
            )
            
    # 2. Hash mật khẩu và tạo bản ghi User mới
    new_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        hashed_password=hash_password(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=TokenResponse, summary="Đăng nhập tài khoản & Nhận JWT Token")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập hệ thống:
    - Kiểm tra thông tin đăng nhập theo username hoặc email
    - So khớp mật khẩu với hàm băm bcrypt
    - Trả về Access Token chuẩn JWT thực tế (thay cho mock token)
    """
    identifier = user_in.username.strip()
    user = db.query(User).filter(
        or_(User.username == identifier, User.email == identifier.lower())
    ).first()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Tạo JWT Access Token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse, summary="Lấy thông tin tài khoản đang đăng nhập")
def get_profile(current_user: User = Depends(get_current_user)):
    """Lấy thông tin người dùng từ JWT Token hợp lệ."""
    return current_user

