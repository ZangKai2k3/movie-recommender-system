"""
Module xử lý luồng dữ liệu mở chính thức từ IMDb (IMDb Open Dataset Streamer).
Kỹ thuật: Đọc giải nén gzip trực tiếp từ luồng mạng HTTP theo từng dòng (Chunked Streaming),
không tải file lớn xuống ổ cứng, xử lý hàng triệu bản ghi trong bộ nhớ chỉ mất vài chục giây.
"""

import gzip
import time
import urllib.request
from typing import Dict, List, Tuple, Set
import logging

class IMDbDataStreamer:
    """Bộ nạp và xử lý luồng dữ liệu nén tsv.gz từ IMDb Data Services."""
    
    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        
    def stream_and_rank_ratings(self, limit: int, min_votes: int) -> Tuple[Dict[str, Tuple[float, int]], Set[str]]:
        """
        Bước 1: Quét luồng `title.ratings.tsv.gz` để lấy điểm đánh giá và xếp hạng theo độ phổ biến.
        
        Tham số:
            limit (int): Số lượng phim mục tiêu cần lấy
            min_votes (int): Ngưỡng số lượt bình chọn tối thiểu
            
        Trả về:
            ratings: Dict {tconst: (averageRating, numVotes)}
            candidate_ids: Set các mã phim top đầu (có kích thước đệm để bù trừ lọc thể loại)
        """
        self.logger.info(f"--- [Bước 1/4] Đang quét luồng đánh giá IMDb (Ratings) - Ngưỡng tối thiểu: {min_votes:,} votes ---")
        t0 = time.time()
        
        req = urllib.request.Request(
            self.config.RATINGS_URL,
            headers={"User-Agent": self.config.USER_AGENT}
        )
        
        ratings: Dict[str, Tuple[float, int]] = {}
        
        # Đọc trực tiếp luồng gzip qua mạng mà không cần ghi file tạm
        with urllib.request.urlopen(req, timeout=self.config.REQUEST_TIMEOUT * 3) as response:
            with gzip.GzipFile(fileobj=response) as gz_stream:
                # Bỏ qua dòng tiêu đề: tconst \t averageRating \t numVotes
                gz_stream.readline()
                
                for line in gz_stream:
                    parts = line.decode("utf-8").strip().split("\t")
                    if len(parts) == 3:
                        tconst = parts[0]
                        votes = int(parts[2])
                        if votes >= min_votes:
                            avg_rating = float(parts[1])
                            ratings[tconst] = (avg_rating, votes)
                            
        elapsed = time.time() - t0
        self.logger.info(f"Đã nạp {len(ratings):,} phim đạt chuẩn >= {min_votes:,} votes trong {elapsed:.2f} giây.")
        
        # Sắp xếp các phim theo số lượt votes giảm dần (độ phổ biến cao nhất)
        sorted_ratings = sorted(ratings.items(), key=lambda item: item[1][1], reverse=True)
        
        # Lấy một khoảng đệm an toàn (gấp 2.2 lần mục tiêu) để bù đắp các phim ngắn/series bị lọc ở bước sau
        buffer_size = min(len(sorted_ratings), max(int(limit * 2.2), limit + 2500))
        candidate_ids: Set[str] = {item[0] for item in sorted_ratings[:buffer_size]}
        
        return ratings, candidate_ids

    def stream_movie_basics(self, candidate_ids: Set[str], ratings: Dict[str, Tuple[float, int]], limit: int) -> List[Dict]:
        """
        Bước 2: Quét luồng `title.basics.tsv.gz` để trích xuất thông tin chi tiết các phim trong danh sách ứng viên.
        
        Lọc:
        - Chỉ giữ lại phim điện ảnh/phim truyện (movie, tvMovie)
        - Không lấy phim người lớn (isAdult == '0')
        - Trích xuất năm phát hành, thời lượng, danh sách thể loại
        """
        self.logger.info(f"--- [Bước 2/4] Đang quét luồng chi tiết phim IMDb (Basics) cho {len(candidate_ids):,} ứng viên ---")
        t0 = time.time()
        
        req = urllib.request.Request(
            self.config.BASICS_URL,
            headers={"User-Agent": self.config.USER_AGENT}
        )
        
        movies: List[Dict] = []
        
        with urllib.request.urlopen(req, timeout=self.config.REQUEST_TIMEOUT * 6) as response:
            with gzip.GzipFile(fileobj=response) as gz_stream:
                gz_stream.readline()  # Bỏ qua dòng tiêu đề
                
                for line in gz_stream:
                    parts = line.decode("utf-8").strip().split("\t")
                    tconst = parts[0]
                    
                    # Chỉ kiểm tra nếu mã phim nằm trong tập hợp ứng viên top đầu
                    if tconst in candidate_ids:
                        title_type = parts[1]
                        is_adult = parts[4]
                        
                        # Áp dụng bộ lọc loại phim và nội dung người lớn
                        if title_type in self.config.ALLOWED_TITLE_TYPES and is_adult == "0":
                            rating, votes = ratings[tconst]
                            primary_title = parts[2]
                            original_title = parts[3]
                            year = parts[5] if parts[5] != "\\N" else ""
                            runtime = int(parts[7]) if parts[7] != "\\N" else 0
                            
                            # Tách chuỗi thể loại thành list
                            genres_raw = parts[8] if parts[8] != "\\N" else ""
                            genres_list = [g.strip() for g in genres_raw.split(",") if g.strip()]
                            
                            movies.append({
                                "id": tconst,
                                "title": primary_title,
                                "original_title": original_title,
                                "year": year,
                                "runtime_minutes": runtime,
                                "genres": genres_list,
                                "rating": rating,
                                "votes": votes,
                                "stars": "",
                                "cast": [],
                                "plot": "",
                                "poster_url": "",
                                "imdb_url": f"https://www.imdb.com/title/{tconst}/"
                            })
                            
        elapsed = time.time() - t0
        self.logger.info(f"Đã trích xuất xong {len(movies):,} phim hợp lệ từ IMDb Basics trong {elapsed:.2f} giây.")
        
        # Sắp xếp lại lần cuối theo số lượt votes giảm dần và lấy đúng số lượng mục tiêu
        movies.sort(key=lambda m: m["votes"], reverse=True)
        final_selected = movies[:limit]
        
        self.logger.info(f"Đã chọn ra top {len(final_selected):,} bộ phim thịnh hành nhất để xử lý tiếp.")
        return final_selected

