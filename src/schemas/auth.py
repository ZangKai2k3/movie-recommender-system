"""
Định nghĩa các Pydantic Schemas phục vụ Xác thực người dùng (Auth).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):
    """Schema yêu cầu khi người dùng Đăng ký tài khoản mới."""
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    email: EmailStr = Field(..., description="Địa chỉ Email hợp lệ")
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")

class UserLogin(BaseModel):
    """Schema yêu cầu khi người dùng Đăng nhập."""
    username: str = Field(..., description="Tên đăng nhập hoặc Email")
    password: str = Field(..., description="Mật khẩu")

class UserResponse(BaseModel):
    """Schema thông tin người dùng trả về cho Frontend (không kèm hashed_password)."""
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """Schema trả về khi Đăng nhập thành công gồm JWT token và thông tin User."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

