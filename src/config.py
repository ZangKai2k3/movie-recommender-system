# -*- coding: utf-8 -*-
"""
Module cấu hình tập trung cho toàn bộ hệ thống (Centralized Configuration).
Đọc các biến môi trường từ hệ thống hoặc file .env với giá trị mặc định an toàn.
"""

import os
from typing import List

# Cấu hình môi trường hoạt động (development | staging | production)
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# Khóa bí mật dùng để ký và xác thực JWT token
# CẢNH BÁO BẢO MẬT: Trong môi trường Production, bắt buộc phải đặt biến môi trường JWT_SECRET_KEY
DEFAULT_DEV_SECRET = "htgoiyphim_dev_only_jwt_secret_key_change_in_production_32bytes"
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", DEFAULT_DEV_SECRET)

if ENVIRONMENT == "production" and JWT_SECRET_KEY == DEFAULT_DEV_SECRET:
    raise RuntimeError("CẢNH BÁO BẢO MẬT: Không được dùng secret mặc định trong môi trường production! Hãy thiết lập biến môi trường JWT_SECRET_KEY.")

# Thuật toán mã hóa JWT
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# Thời hạn hiệu lực của JWT Access Token (tính theo phút, mặc định 7 ngày = 10080 phút)
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

# Cấu hình cơ sở dữ liệu SQLite / PostgreSQL
DB_DIR: str = os.getenv("DB_DIR", "./data")
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DB_DIR, 'htgoiyphim.db')}")

# Cấu hình CORS - Cho phép các domain nào gọi API
# Mặc định cho phép Frontend React chạy ở localhost:3000 và 127.0.0.1:3000
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173")
CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Đường dẫn file dữ liệu phim đã xử lý
DATA_PATH_DEFAULT = "data/processed/movies_10000.csv"
DATA_PATH: str = os.getenv("DATA_PATH", DATA_PATH_DEFAULT)
if not os.path.exists(DATA_PATH):
    pdir = "data/processed"
    if os.path.exists(pdir):
        csvs = [os.path.join(pdir, f) for f in os.listdir(pdir) if f.endswith(".csv")]
        if csvs:
            DATA_PATH = csvs[0]

