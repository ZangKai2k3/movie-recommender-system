"""
Điểm khởi tạo ứng dụng Web API FastAPI cho Hệ Thống Gợi Ý Phim (HTGoiYPhim).
Bao gồm: Cấu hình CORS, tự động khởi tạo bảng CSDL SQLite, nạp các API Routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database.connection import Base, engine
from .api.auth_router import router as auth_router
from .api.history_router import router as history_router
from .api.rating_router import router as rating_router
from .api.movie_router import router as movie_router

# 1. Tự động tạo các bảng CSDL SQLite (users, watch_history, ratings) nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

# 2. Khởi tạo FastAPI App
app = FastAPI(
    title="Hệ Thống Gợi Ý Phim API (HTGoiYPhim)",
    description="Hệ thống Backend cung cấp dịch vụ Xác thực người dùng, Lịch sử xem phim, Đánh giá phim và Thuật toán Gợi ý phim thông minh.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. Cấu hình CORS an toàn theo danh sách domain cấu hình
# Sử dụng allow_origins rõ ràng để đảm bảo tương thích chuẩn bảo mật trình duyệt
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Gắn các Routers vào ứng dụng
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(rating_router)
app.include_router(movie_router)

@app.get("/", tags=["Trang chủ"])
def root():
    """Endpoint kiểm tra trạng thái hoạt động của hệ thống (Health Check)."""
    return {
        "system": "HTGoiYPhim API",
        "status": "Online",
        "version": "2.0.0",
        "database": "SQLite (SQLAlchemy)",
        "docs_url": "/docs"
    }

