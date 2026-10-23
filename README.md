# Hệ Thống Gợi Ý Phim (HTGoiYPhim)

Hệ thống Gợi ý Phim xây dựng hoàn chỉnh từ A-Z với kiến trúc hiện đại:
- **Crawler**: Thu thập & làm giàu dữ liệu phim tốc độ cao từ IMDb & Wikipedia.
- **AI Recommender**: Thuật toán Content-Based Filtering (TF-IDF + Cosine Similarity).
- **Backend API**: FastAPI + Cơ sở dữ liệu SQLite qua SQLAlchemy ORM.
- **Authentication**: Đăng ký, Đăng nhập, băm mật khẩu chuẩn `bcrypt` và sinh mã `JWT Token` thực tế.
- **User Interactions**: Lưu lịch sử xem phim (`WatchHistory`) & Đánh giá sao (`Rating`).
- **Frontend**: Giao diện người dùng ReactJS tối ưu trải nghiệm (xem phim, đánh giá, gợi ý tương đồng).
- **Deployment**: Đóng gói Docker Compose chạy toàn bộ hệ thống bằng 1 lệnh duy nhất.

---

## Cấu Trúc Dự Án

```
HTGoiYPhim/
├── data/
│   ├── htgoiyphim.db        # Cơ sở dữ liệu SQLite (tự động khởi tạo)
│   ├── raw/                 # Lưu trữ checkpoint tiến trình crawler
│   └── processed/           # Tập dữ liệu phim (movies_10000.csv & .json)
├── frontend/                # Ứng dụng giao diện ReactJS
│   ├── public/
│   ├── src/                 # Giao diện người dùng (Tabs, Cards, Modals)
│   ├── nginx.conf           # Cấu hình Nginx reverse proxy sang Backend
│   ├── package.json
│   └── Dockerfile           # Multi-stage build (Node build -> Nginx Alpine)
├── src/
│   ├── api/                 # Các API Routers của FastAPI
│   │   ├── auth_router.py   # /api/auth (register, login, me)
│   │   ├── history_router.py# /api/history (POST xem phim, GET danh sách)
│   │   ├── rating_router.py # /api/ratings (POST chấm điểm, GET danh sách)
│   │   └── movie_router.py  # /api/movies & /api/movies/recommendations
│   ├── auth/                # Bảo mật & JWT
│   │   ├── security.py      # Băm mật khẩu bcrypt, sinh & giải mã JWT
│   │   └── dependencies.py  # Dependency get_current_user
│   ├── database/            # CSDL SQLite & SQLAlchemy ORM
│   │   ├── connection.py    # Engine, SessionLocal, Base, get_db
│   │   └── models.py        # Các bảng User, WatchHistory, Rating
│   ├── schemas/             # Pydantic Schemas validate dữ liệu
│   │   ├── auth.py          # UserCreate, UserLogin, TokenResponse...
│   │   └── interaction.py   # HistoryCreate, RatingCreate...
│   ├── crawler/             # Module cào dữ liệu phim IMDb tốc độ cao
│   ├── recommender/         # Thuật toán gợi ý Content-Based Filtering
│   ├── utils/
│   │   └── logger.py        # Bộ ghi log chuẩn Unicode
│   └── main.py              # Ứng dụng chính FastAPI & cấu hình CORS
├── Dockerfile               # Dockerfile cho Backend FastAPI
├── docker-compose.yml       # Đóng gói và chạy đồng thời cả Frontend & Backend
├── requirements.txt         # Danh sách thư viện Python
├── run_server.py            # Chạy Backend server (Uvicorn port 8000)
├── run_crawler.py           # Chạy cào dữ liệu phim
└── recommend.py             # CLI test thuật toán gợi ý phim
```

---

## Danh Sách Các API Endpoints Chính

| Phương thức | Đường dẫn | Mô tả | Yêu cầu Token? |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Đăng ký tài khoản người dùng mới (username, email, password) | Không |
| `POST` | `/api/auth/login` | Đăng nhập và nhận chuỗi JWT Access Token thực tế | Không |
| `GET` | `/api/auth/me` | Lấy thông tin tài khoản hiện tại | **Có (Bearer)** |
| `POST` | `/api/history` | Lưu lại lịch sử khi người dùng xem 1 bộ phim | **Có (Bearer)** |
| `GET` | `/api/history` | Lấy danh sách phim đã xem gần đây (sắp xếp mới nhất) | **Có (Bearer)** |
| `POST` | `/api/ratings` | Gửi đánh giá sao (1-10) cho bộ phim | **Có (Bearer)** |
| `GET` | `/api/ratings` | Lấy danh sách phim người dùng đã đánh giá | **Có (Bearer)** |
| `GET` | `/api/movies` | Danh sách phim thịnh hành (có phân trang & tìm kiếm) | Không |
| `GET` | `/api/movies/recommendations` | Gợi ý phim tương đồng theo tên phim đã chọn | Không |

---

## Hướng Dẫn Chạy Toàn Bộ Hệ Thống

### Cách 1: Chạy bằng Docker Compose (Khuyên Dùng cho Production)
Yêu cầu đã cài đặt Docker & Docker Compose. Mở terminal tại thư mục gốc và chạy:

```bash
docker-compose up --build
```

Sau khi khởi chạy:
- **Giao diện Web (Frontend ReactJS)**: Truy cập `http://localhost`
- **Backend API & Swagger Docs**: Truy cập `http://localhost:8000/docs`

---

### Cách 2: Chạy trực tiếp trên máy (Development)

#### 1. Khởi chạy Backend FastAPI
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy server API (cổng 8000)
python run_server.py
```
*Truy cập tài liệu API tự động tại: `http://localhost:8000/docs`*

#### 2. Khởi chạy Frontend ReactJS (Tùy chọn nếu muốn chạy dev server)
```bash
cd frontend
npm install
npm start
```
*Giao diện sẽ tự động mở tại: `http://localhost:3000`*
