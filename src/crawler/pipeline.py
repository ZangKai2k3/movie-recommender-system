"""
Module điều phối Pipeline tổng thể (Movie Crawler Pipeline Coordinator).
Tích hợp toàn bộ các giai đoạn từ thu thập luồng IMDb, làm giàu đa luồng,
xử lý đặc trưng gợi ý đến cơ chế lưu tiến trình (checkpoint) và xuất file.
"""

import os
import json
import time
from typing import List, Dict, Optional
import logging

from .config import CrawlerConfig
from .imdb_stream import IMDbDataStreamer
from .enricher import MovieEnricher
from .preprocessor import MovieDataPreprocessor

class MovieCrawlerPipeline:
    """Đầu não điều khiển toàn bộ tiến trình thu thập và xử lý dữ liệu phim."""
    
    def __init__(self, config: Optional[CrawlerConfig] = None, logger: Optional[logging.Logger] = None):
        self.config = config or CrawlerConfig()
        self.config.ensure_directories()
        
        self.logger = logger or logging.getLogger("MovieCrawlerPipeline")
        
        # Khởi tạo các module thành phần
        self.streamer = IMDbDataStreamer(self.config, self.logger)
        self.enricher = MovieEnricher(self.config, self.logger)
        self.preprocessor = MovieDataPreprocessor(self.logger)
        
    def _get_checkpoint_path(self, limit: int) -> str:
        """Đường dẫn lưu file checkpoint tiến trình."""
        return os.path.join(self.config.DATA_RAW_DIR, f"checkpoint_{limit}_movies.json")

    def _load_checkpoint(self, checkpoint_path: str) -> Dict[str, Dict]:
        """Tải dữ liệu checkpoint cũ để tiếp tục phiên chạy trước đó."""
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {m["id"]: m for m in data if "id" in m}
                    elif isinstance(data, dict):
                        return data
            except Exception as e:
                self.logger.warning(f"Không thể đọc checkpoint cũ: {e}")
        return {}

    def _save_checkpoint(self, checkpoint_path: str, movies: List[Dict]):
        """Lưu trạng thái dữ liệu hiện tại vào file checkpoint."""
        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(movies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu checkpoint: {e}")

    def execute(
        self,
        limit: int = 10000,
        min_votes: Optional[int] = None,
        enrich_data: bool = True,
        workers: Optional[int] = None,
        output_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Thực thi toàn bộ quy trình từ A - Z.
        
        Tham số:
            limit (int): Số lượng phim cần thu thập
            min_votes (int, optional): Ngưỡng vote tối thiểu
            enrich_data (bool): Có tải thêm Poster, Diễn viên và Cốt truyện không
            workers (int, optional): Số luồng đồng thời
            output_name (str, optional): Tên file xuất ra
            
        Trả về:
            List[Dict]: Danh sách dữ liệu các bộ phim đã sẵn sàng cho hệ thống gợi ý
        """
        start_time = time.time()
        votes_threshold = min_votes if min_votes is not None else self.config.MIN_VOTES
        file_prefix = output_name or f"movies_{limit}"
        checkpoint_path = self._get_checkpoint_path(limit)
        
        self.logger.info("==================================================================")
        self.logger.info(f" KHỞI ĐỘNG PIPELINE THU THẬP DỮ LIỆU PHIM (Mục tiêu: {limit:,} phim)")
        self.logger.info(f" - Ngưỡng bình chọn tối thiểu : >= {votes_threshold:,} votes")
        self.logger.info(f" - Bổ sung Poster & Cốt truyện : {'BẬT' if enrich_data else 'TẮT'}")
        self.logger.info(f" - Số luồng thực thi           : {workers or self.config.MAX_WORKERS} workers")
        self.logger.info("==================================================================")
        
        # 1. Quét luồng Ratings từ IMDb & Lọc top ứng viên
        ratings, candidate_ids = self.streamer.stream_and_rank_ratings(limit=limit, min_votes=votes_threshold)
        
        # 2. Quét luồng Basics từ IMDb để lấy siêu dữ liệu cơ bản
        movies = self.streamer.stream_movie_basics(candidate_ids=candidate_ids, ratings=ratings, limit=limit)
        
        # 3. Làm giàu dữ liệu (Poster, Diễn viên chính, Tóm tắt cốt truyện Wikipedia)
        if enrich_data:
            cached_data = self._load_checkpoint(checkpoint_path)
            if cached_data:
                self.logger.info(f"Đã nạp {len(cached_data):,} bản ghi từ checkpoint trước đó.")
                
            def on_checkpoint(current_movies):
                self._save_checkpoint(checkpoint_path, current_movies)
                
            movies = self.enricher.enrich_movies_concurrently(
                movies=movies,
                existing_progress=cached_data,
                checkpoint_callback=on_checkpoint,
                max_workers=workers
            )
            
        # 4. Tiền xử lý & Trích xuất đặc trưng phục vụ Gợi ý phim
        movies = self.preprocessor.transform_for_recommendation(movies)
        
        # 5. Xuất tập dữ liệu ra file
        self.preprocessor.export_data(
            movies=movies,
            output_dir=self.config.DATA_PROCESSED_DIR,
            file_prefix=file_prefix
        )
        
        total_time = time.time() - start_time
        self.logger.info(f"Toàn bộ pipeline hoàn tất trong {total_time:.1f}s ({total_time/60:.2f} phút).")
        return movies

