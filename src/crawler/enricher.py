"""
Module bổ sung thông tin chi tiết phim (Enrichment Module).
Kỹ thuật: Sử dụng Đa luồng (Concurrent ThreadPoolExecutor) kết hợp 2 nguồn dữ liệu tốc độ cao:
1. IMDb CDN Suggestion API: Lấy ảnh bìa Poster chính thức độ phân giải cao và dàn diễn viên chính (Stars).
2. Wikipedia API: Lấy đoạn văn bản tóm tắt cốt truyện (Plot Summary) mở rộng phục vụ cho mô hình NLP.
"""

import json
import urllib.request
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
import logging
from tqdm import tqdm

class MovieEnricher:
    """Bộ làm giàu dữ liệu phim đa luồng không cần Selenium."""
    
    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        
    def _fetch_imdb_cdn_metadata(self, movie_id: str) -> Dict[str, str]:
        """
        Gọi endpoint CDN của IMDb để lấy Poster và Diễn viên chính.
        Endpoint này cực nhanh, trả về JSON trực tiếp mà không cần cào HTML.
        """
        url = self.config.IMDB_SUGGEST_URL_TEMPLATE.format(id=movie_id)
        req = urllib.request.Request(url, headers={"User-Agent": self.config.USER_AGENT})
        
        result = {"poster_url": "", "stars": "", "cast": []}
        try:
            with urllib.request.urlopen(req, timeout=self.config.REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("d", [])
                
                # Tìm đúng mục khớp với ID của phim
                for item in items:
                    if item.get("id") == movie_id:
                        # Lấy link ảnh poster chất lượng cao
                        image_info = item.get("i", {})
                        if isinstance(image_info, dict) and "imageUrl" in image_info:
                            result["poster_url"] = image_info["imageUrl"]
                            
                        # Lấy danh sách diễn viên chính (stars)
                        stars_str = item.get("s", "")
                        if stars_str:
                            result["stars"] = stars_str
                            result["cast"] = [name.strip() for name in stars_str.split(",") if name.strip()]
                        break
        except Exception:
            pass
            
        return result

    def _fetch_wikipedia_plot(self, title: str, year: str) -> str:
        """
        Gọi API Wikipedia để lấy đoạn tóm tắt mở đầu (extract intro) của bộ phim.
        Thử nghiệm các từ khóa phổ biến để đảm bảo tỷ lệ tìm thấy cao nhất.
        """
        queries = []
        if year:
            queries.append(f"{title} ({year} film)")
            queries.append(f"{title} (film)")
        queries.append(title)
        
        for q in queries:
            try:
                api_url = (
                    f"{self.config.WIKIPEDIA_API_URL}"
                    f"?action=query&prop=extracts&exintro=true&explaintext=true"
                    f"&titles={quote(q)}&format=json"
                )
                req = urllib.request.Request(
                    api_url,
                    headers={"User-Agent": "MovieRecommendationBot/2.0 (research@university.edu)"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        if pid != "-1":
                            extract = pdata.get("extract", "").strip()
                            if extract and len(extract) > 40:
                                return extract
            except Exception:
                pass
                
        return ""

    def enrich_single_movie(self, movie: Dict) -> Dict:
        """Bổ sung Poster, Stars và Plot cho một bản ghi phim duy nhất."""
        movie_id = movie["id"]
        
        # 1. Bổ sung Poster và Diễn viên (nếu chưa có)
        if not movie.get("poster_url") or not movie.get("stars"):
            cdn_data = self._fetch_imdb_cdn_metadata(movie_id)
            if cdn_data["poster_url"]:
                movie["poster_url"] = cdn_data["poster_url"]
            if cdn_data["stars"]:
                movie["stars"] = cdn_data["stars"]
                movie["cast"] = cdn_data["cast"]
                
        # 2. Bổ sung Tóm tắt cốt truyện (nếu chưa có)
        if not movie.get("plot"):
            plot_text = self._fetch_wikipedia_plot(movie["title"], movie.get("year", ""))
            if plot_text:
                movie["plot"] = plot_text
                
        return movie

    def enrich_movies_concurrently(
        self,
        movies: List[Dict],
        existing_progress: Optional[Dict[str, Dict]] = None,
        checkpoint_callback: Optional[Callable[[List[Dict]], None]] = None,
        max_workers: Optional[int] = None
    ) -> List[Dict]:
        """
        Thực hiện bổ sung dữ liệu đồng thời trên toàn bộ danh sách phim bằng ThreadPoolExecutor.
        Tự động tái sử dụng dữ liệu đã nạp từ checkpoint để tiết kiệm thời gian.
        """
        workers = max_workers or self.config.MAX_WORKERS
        self.logger.info(f"--- [Bước 3/4] Bắt đầu bổ sung Poster, Diễn viên & Cốt truyện ({len(movies):,} phim, {workers} luồng) ---")
        
        # Đồng bộ hóa với dữ liệu checkpoint đã lưu trước đó nếu có
        existing_progress = existing_progress or {}
        to_process = []
        for m in movies:
            mid = m["id"]
            if mid in existing_progress:
                cached = existing_progress[mid]
                if cached.get("plot"):
                    m["plot"] = cached["plot"]
                if cached.get("poster_url"):
                    m["poster_url"] = cached["poster_url"]
                if cached.get("stars"):
                    m["stars"] = cached["stars"]
                    m["cast"] = cached.get("cast", [])
                    
            # Nếu còn thiếu ít nhất 1 thông tin (plot hoặc poster) thì đưa vào danh sách cần xử lý
            if not m.get("plot") or not m.get("poster_url"):
                to_process.append(m)
                
        self.logger.info(f"{len(movies) - len(to_process):,} phim đã có sẵn dữ liệu. Đang xử lý {len(to_process):,} phim còn lại...")
        
        if not to_process:
            return movies
            
        enriched_count = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_movie = {executor.submit(self.enrich_single_movie, m): m for m in to_process}
            pbar = tqdm(total=len(to_process), desc="Đang làm giàu dữ liệu", unit="phim")
            
            processed = 0
            for future in as_completed(future_to_movie):
                movie = future_to_movie[future]
                try:
                    updated_movie = future.result()
                    if updated_movie.get("plot") or updated_movie.get("poster_url"):
                        enriched_count += 1
                except Exception as e:
                    self.logger.debug(f"Lỗi khi làm giàu phim {movie.get('title')}: {e}")
                    
                processed += 1
                pbar.update(1)
                
                # Lưu checkpoint định kỳ sau mỗi 100 phim xử lý
                if checkpoint_callback and processed % 100 == 0:
                    checkpoint_callback(movies)
                    
            pbar.close()
            
        self.logger.info(f"Hoàn thành làm giàu dữ liệu. Đã cập nhật thành công cho {enriched_count:,} bộ phim.")
        if checkpoint_callback:
            checkpoint_callback(movies)
            
        return movies

