"""
Module cấu hình trung tâm cho bộ cào dữ liệu phim (IMDb & Enrichment).
Chứa các URL tập dữ liệu, header giả lập, đường dẫn lưu trữ và các ngưỡng lọc dữ liệu.
"""

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class CrawlerConfig:
    """Lớp lưu trữ toàn bộ tham số cấu hình cho Crawler Pipeline."""
    
    # 1. Nguồn tập dữ liệu chính thức từ IMDb (Cập nhật hàng ngày, nén tsv.gz)
    RATINGS_URL: str = "https://datasets.imdbws.com/title.ratings.tsv.gz"
    BASICS_URL: str = "https://datasets.imdbws.com/title.basics.tsv.gz"
    
    # 2. Endpoints bổ sung thông tin (Enrichment)
    # IMDb CDN Suggestion API: Cung cấp poster chính thức và diễn viên chính siêu nhanh dạng JSON
    IMDB_SUGGEST_URL_TEMPLATE: str = "https://v3.sg.media-imdb.com/suggestion/x/{id}.json"
    # Wikipedia API: Cung cấp đoạn văn bản tóm tắt cốt truyện mở rộng phục vụ NLP
    WIKIPEDIA_API_URL: str = "https://en.wikipedia.org/w/api.php"
    
    # 3. Tiêu chí lọc chất lượng dữ liệu phục vụ Hệ thống Gợi ý
    MIN_VOTES: int = 1000                      # Số lượt đánh giá tối thiểu để lọc phim có độ tin cậy cao
    ALLOWED_TITLE_TYPES: tuple = ("movie", "tvMovie")  # Chỉ lấy phim điện ảnh, bỏ qua series dài tập/phim ngắn
    EXCLUDE_ADULT: bool = True                 # Loại bỏ phim có nội dung người lớn
    
    # 4. Cấu hình luồng và mạng
    MAX_WORKERS: int = 12                      # Số luồng đồng thời khi enrich poster & tóm tắt
    REQUEST_TIMEOUT: int = 10                  # Thời gian timeout mỗi HTTP request (giây)
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    
    # 5. Đường dẫn thư mục
    DATA_RAW_DIR: str = "./data/raw"
    DATA_PROCESSED_DIR: str = "./data/processed"
    LOGS_DIR: str = "./logs"
    
    def ensure_directories(self):
        """Tạo sẵn các thư mục cần thiết nếu chưa có."""
        for path in [self.DATA_RAW_DIR, self.DATA_PROCESSED_DIR, self.LOGS_DIR]:
            os.makedirs(path, exist_ok=True)

