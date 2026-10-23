"""
Module tiền xử lý và trích chọn đặc trưng cho Hệ Thống Gợi Ý Phim (Feature Engineering).
Mục đích:
1. Chuẩn hóa chuỗi văn bản cho thể loại, diễn viên và cốt truyện.
2. Nối đặc trưng thành trường `combined_features` ("Metadata Soup") để làm đầu vào cho TF-IDF / Embedding / Cosine Similarity.
3. Tính toán điểm xếp hạng có trọng số IMDb Bayesian Weighted Rating (WR) để xếp hạng phim chuẩn xác.
4. Xuất dữ liệu ra file JSON và CSV (hỗ trợ hiển thị tiếng Việt trên Excel với utf-8-sig).
"""

import json
import os
import re
from typing import List, Dict
import pandas as pd
import logging

class MovieDataPreprocessor:
    """Bộ xử lý dữ liệu và tạo đặc trưng chuyên biệt cho thuật toán gợi ý phim."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def _clean_text(self, text: str) -> str:
        """Làm sạch ký tự thừa, khoảng trắng và chuẩn hóa chữ thường."""
        if not text:
            return ""
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned.strip()

    def _normalize_name_token(self, name: str) -> str:
        """
        Nối các từ trong tên diễn viên bằng dấu gạch dưới (ví dụ: 'Tom Hanks' -> 'Tom_Hanks').
        Kỹ thuật này giúp bộ tách từ (Tokenizer) của TF-IDF không bị chia cắt họ tên diễn viên thành các từ đơn vô nghĩa.
        """
        return name.strip().replace(" ", "_")

    def transform_for_recommendation(self, movies: List[Dict]) -> List[Dict]:
        """
        Tạo các cột đặc trưng quan trọng cho hệ thống gợi ý Content-Based Filtering.
        """
        self.logger.info("--- [Bước 4/4] Đang xử lý đặc trưng cho Hệ Thống Gợi Ý (Feature Engineering) ---")
        
        # 1. Tính toán điểm chuẩn trung bình (C) và số vote tối thiểu (m) để tính điểm Weighted Rating
        all_ratings = [m["rating"] for m in movies if m.get("rating")]
        all_votes = [m["votes"] for m in movies if m.get("votes")]
        
        C = sum(all_ratings) / len(all_ratings) if all_ratings else 6.5
        # Lấy m là phân vị thứ 70 của lượt vote trong tập dữ liệu
        if all_votes:
            sorted_votes = sorted(all_votes)
            m_threshold = sorted_votes[int(len(sorted_votes) * 0.7)]
        else:
            m_threshold = 1000
            
        for movie in movies:
            title = self._clean_text(movie.get("title", ""))
            genres_list = movie.get("genres", [])
            genres_text = " ".join(genres_list)
            
            # Diễn viên: nối từ để giữ nguyên thực thể tên (Named Entity)
            cast_list = movie.get("cast", [])
            cast_normalized = [self._normalize_name_token(name) for name in cast_list]
            cast_text = " ".join(cast_normalized)
            
            plot_text = self._clean_text(movie.get("plot", ""))
            
            # Gán các trường đặc trưng rõ ràng
            movie["genres_text"] = genres_text
            movie["cast_text"] = cast_text
            movie["plot_clean"] = plot_text
            
            # Chuỗi đặc trưng tổng hợp ("Soup") dùng cho TF-IDF / Cosine Similarity
            # Kết hợp: Tên phim + 2x Thể loại (tăng trọng số) + Diễn viên + Tóm tắt cốt truyện
            combined = f"{title} {genres_text} {genres_text} {cast_text} {plot_text}".strip()
            movie["combined_features"] = combined
            movie["feature_length"] = len(combined)
            
            # Tính điểm đánh giá theo trọng số Bayesian IMDb:
            # WR = (v / (v + m)) * R + (m / (v + m)) * C
            v = movie.get("votes", 0)
            R = movie.get("rating", 0.0)
            weighted_rating = (v / (v + m_threshold)) * R + (m_threshold / (v + m_threshold)) * C
            movie["weighted_rating"] = round(weighted_rating, 2)
            
        self.logger.info(f"Đã xử lý đặc trưng hoàn chỉnh cho {len(movies):,} bộ phim.")
        return movies

    def export_data(self, movies: List[Dict], output_dir: str, file_prefix: str = "movies"):
        """
        Xuất tập dữ liệu ra cả hai định dạng:
        1. JSON: Lưu trữ đầy đủ cấu trúc dữ liệu nguyên bản dạng mảng/từ điển.
        2. CSV: Xuất định dạng bảng tương thích chuẩn với Pandas và Excel (utf-8-sig).
        """
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"{file_prefix}.json")
        csv_path = os.path.join(output_dir, f"{file_prefix}.csv")
        
        self.logger.info(f"Đang xuất kết quả ra {json_path} và {csv_path}...")
        
        # Xuất JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
            
        # Chuyển đổi và xuất CSV
        df = pd.DataFrame(movies)
        
        # Chuyển đổi các cột kiểu danh sách sang dạng chuỗi ngăn cách bởi dấu phẩy
        for col in ["genres", "cast"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x or ""))
                
        # Sắp xếp các cột theo thứ tự dễ nhìn nhất khi mở bằng Excel
        priority_cols = [
            "id", "title", "year", "rating", "votes", "weighted_rating",
            "genres", "cast", "plot_clean", "poster_url", "imdb_url", "combined_features"
        ]
        existing_cols = [col for col in priority_cols if col in df.columns]
        other_cols = [col for col in df.columns if col not in priority_cols]
        df = df[existing_cols + other_cols]
        
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"Xuất file thành công: {len(movies):,} bản ghi tại {csv_path}")
        print(f"\n==================================================================")
        print(f" [HOÀN TẤT THU THẬP DỮ LIỆU]")
        print(f" - Tổng số bản ghi : {len(movies):,} phim")
        print(f" - Tập tin JSON   : {os.path.abspath(json_path)}")
        print(f" - Tập tin CSV    : {os.path.abspath(csv_path)}")
        print(f"==================================================================\n")

