# -*- coding: utf-8 -*-
"""
Mô hình Gợi ý Phim dựa trên Nội dung (Content-Based Filtering Recommender).
Sử dụng ma trận TF-IDF Vectorizer và Cosine Similarity tính toán độ tương đồng giữa các phim
dựa trên trường đặc trưng `combined_features` (Tên phim + Thể loại + Diễn viên + Cốt truyện).
Hỗ trợ cả scikit-learn (tối ưu tốc độ) và cơ chế thuần NumPy dự phòng (không phụ thuộc thư viện ngoài).
Bổ sung cơ chế giải thích lý do gợi ý (Explainable AI) dựa trên dữ liệu thực tế.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Optional, Set
import numpy as np
import pandas as pd

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class ContentBasedRecommender:
    """Thuật toán gợi ý phim tương đồng bằng TF-IDF, Cosine Similarity và Điểm trọng số Bayesian."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.df = None
        self.indices = None
        self._load_data()
        
        if SKLEARN_AVAILABLE:
            self._fit_sklearn()
        else:
            self._fit_numpy()

    def _load_data(self):
        """Đọc và chuẩn hóa dữ liệu từ file CSV hoặc JSON."""
        if self.dataset_path.endswith(".csv"):
            self.df = pd.read_csv(self.dataset_path).fillna("")
        else:
            self.df = pd.read_json(self.dataset_path).fillna("")
            
        # Chuẩn hóa cột weighted_rating về thang [0, 1] để dùng cho xếp hạng kết hợp (Hybrid Ranking)
        if "weighted_rating" in self.df.columns:
            wr_series = pd.to_numeric(self.df["weighted_rating"], errors="coerce").fillna(5.0)
            wr_min = wr_series.min()
            wr_max = wr_series.max()
            if wr_max > wr_min:
                self.df["norm_wr"] = (wr_series - wr_min) / (wr_max - wr_min)
            else:
                self.df["norm_wr"] = 0.5
        else:
            self.df["norm_wr"] = 0.5
            
        # Tạo bảng tra cứu index theo tên phim (viết thường để tra cứu không phân biệt hoa thường)
        self.indices = pd.Series(self.df.index, index=self.df["title"].str.lower()).drop_duplicates()

    def _fit_sklearn(self):
        """Huấn luyện bằng thư viện scikit-learn (sử dụng ma trận thưa tối ưu bộ nhớ)."""
        self.tfidf = TfidfVectorizer(stop_words="english", max_features=15000)
        self.tfidf_matrix = self.tfidf.fit_transform(self.df["combined_features"])

    def _fit_numpy(self):
        """Bộ tính TF-IDF thuần NumPy dự phòng khi chưa cài đặt scikit-learn."""
        documents = [
            re.findall(r"\b\w+\b", text.lower())
            for text in self.df["combined_features"]
        ]
        num_docs = len(documents)
        
        # 1. Tính Document Frequency (DF)
        df_counts = Counter()
        for doc in documents:
            df_counts.update(set(doc))
            
        # Lấy từ vựng phổ biến (bỏ từ đơn quá ngắn)
        vocab = [word for word, count in df_counts.items() if len(word) > 2 and count >= 1]
        self.vocab_map = {word: i for i, word in enumerate(vocab)}
        num_vocab = len(vocab)
        
        # 2. Tính Inverse Document Frequency (IDF)
        self.idf = np.zeros(num_vocab, dtype=np.float32)
        for word, idx in self.vocab_map.items():
            self.idf[idx] = math.log((1 + num_docs) / (1 + df_counts[word])) + 1.0
            
        # 3. Tính ma trận TF-IDF đậm đặc
        self.tfidf_dense = np.zeros((num_docs, num_vocab), dtype=np.float32)
        for doc_id, doc in enumerate(documents):
            tf = Counter(doc)
            doc_len = len(doc) or 1
            for word, count in tf.items():
                if word in self.vocab_map:
                    v_idx = self.vocab_map[word]
                    self.tfidf_dense[doc_id, v_idx] = (count / doc_len) * self.idf[v_idx]
                    
            # Chuẩn hóa L2 norm
            norm = np.linalg.norm(self.tfidf_dense[doc_id])
            if norm > 0:
                self.tfidf_dense[doc_id] /= norm

    def _generate_recommendation_reason(self, source_movie: Dict, target_movie: Dict, similarity_score: float) -> str:
        """
        Tạo lời giải thích lý do gợi ý minh bạch dựa trên dữ liệu thực tế:
        - So khớp thể loại chung giữa 2 phim.
        - So khớp diễn viên chung nếu có.
        - Đưa ra lý do chính xác không bịa đặt.
        """
        # 1. Trích xuất thể loại chung
        src_raw = str(source_movie.get("genres", ""))
        tgt_raw = str(target_movie.get("genres", ""))
        src_genres = {g.strip().lower() for g in src_raw.split(",") if g.strip()}
        tgt_genres = {g.strip().lower() for g in tgt_raw.split(",") if g.strip()}
        common_genres = [g.capitalize() for g in src_genres.intersection(tgt_genres) if g != "unknown"]
        
        # 2. Trích xuất diễn viên chung nếu có
        src_cast_raw = str(source_movie.get("cast", ""))
        tgt_cast_raw = str(target_movie.get("cast", ""))
        src_cast = {c.strip().lower() for c in src_cast_raw.split(",") if c.strip()}
        tgt_cast = {c.strip().lower() for c in tgt_cast_raw.split(",") if c.strip()}
        common_cast = [c.title() for c in src_cast.intersection(tgt_cast) if c]
        
        # 3. Tạo lời giải thích thực tế
        if common_cast and common_genres:
            return f"Cùng thể loại {', '.join(common_genres[:2])} và có sự tham gia của diễn viên {', '.join(common_cast[:2])}."
        elif common_genres:
            return f"Cùng thể loại {', '.join(common_genres[:3])} với phong cách tương đồng {source_movie.get('title')}."
        elif common_cast:
            return f"Có sự tham gia của diễn viên {', '.join(common_cast[:2])}."
        else:
            return f"Tương đồng về chủ đề cốt truyện (độ tương đồng {(similarity_score * 100):.0f}%)."

    def recommend(self, movie_title: str, top_n: int = 10) -> List[Dict]:
        """
        Tìm kiếm và trả về top N bộ phim có nội dung tương tự nhất với phim đã chọn.
        Áp dụng công thức xếp hạng kết hợp:
        Score = 0.75 * Cosine_Similarity + 0.25 * Normalized_Weighted_Rating
        
        Tham số:
            movie_title (str): Tên phim cần tìm gợi ý
            top_n (int): Số lượng phim gợi ý trả về
            
        Trả về:
            List[Dict]: Danh sách thông tin các phim được gợi ý kèm lý do
        """
        if not movie_title or not movie_title.strip():
            raise ValueError("Vui lòng nhập tên phim cần tìm gợi ý.")
            
        title_lower = movie_title.strip().lower()
        if title_lower not in self.indices:
            matches = self.df[self.df["title"].str.lower().str.contains(title_lower, na=False)]
            if matches.empty:
                raise ValueError(f"Không tìm thấy phim '{movie_title}' trong tập dữ liệu.")
            idx = matches.index[0]
        else:
            idx = self.indices[title_lower]
            
        source_movie = self.df.iloc[idx].to_dict()
        
        # Tính toán độ tương đồng Cô-sin giữa phim này và toàn bộ kho phim
        if SKLEARN_AVAILABLE:
            cosine_sim = linear_kernel(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        else:
            query_vec = self.tfidf_dense[idx]
            cosine_sim = np.dot(self.tfidf_dense, query_vec)
            
        # Áp dụng công thức Hybrid Ranking kết hợp giữa độ tương đồng nội dung (75%) và chất lượng điểm số (25%)
        # Điều này ngăn các phim rác có vài vote nhưng trùng từ khóa không vượt lên trên các phim kinh điển
        norm_wr = self.df["norm_wr"].values
        composite_scores = 0.75 * cosine_sim + 0.25 * norm_wr
        
        # Sắp xếp các phim theo điểm tổng hợp giảm dần
        ranked_indices = composite_scores.argsort()[::-1]
        
        results = []
        seen_titles = {source_movie.get("title", "").strip().lower()}
        
        for i in ranked_indices:
            if i == idx:
                continue
            movie_info = self.df.iloc[i].to_dict()
            m_title = movie_info.get("title", "").strip().lower()
            if m_title in seen_titles:
                continue
            seen_titles.add(m_title)
            
            raw_sim = float(cosine_sim[i])
            movie_info["similarity_score"] = round(raw_sim, 4)
            movie_info["composite_score"] = round(float(composite_scores[i]), 4)
            movie_info["recommendation_reason"] = self._generate_recommendation_reason(source_movie, movie_info, raw_sim)
            
            results.append(movie_info)
            if len(results) >= top_n:
                break
                
        return results

    def recommend_by_text(self, query_text: str, top_n: int = 10) -> List[Dict]:
        """
        Gợi ý phim dựa trên đoạn văn bản / cốt truyện tự do mà người dùng nhập vào.
        Ví dụ: 'astronauts traveling through space to save humanity'
        """
        cleaned_query = query_text.strip().lower()
        if not cleaned_query:
            return []
            
        if SKLEARN_AVAILABLE:
            query_vec = self.tfidf.transform([cleaned_query])
            cosine_sim = linear_kernel(query_vec, self.tfidf_matrix).flatten()
        else:
            tokens = re.findall(r"\b\w+\b", cleaned_query)
            if not tokens:
                return []
            tf = Counter(tokens)
            doc_len = len(tokens)
            num_vocab = len(self.vocab_map)
            query_vec = np.zeros(num_vocab, dtype=np.float32)
            for word, count in tf.items():
                if word in self.vocab_map:
                    v_idx = self.vocab_map[word]
                    query_vec[v_idx] = (count / doc_len) * self.idf[v_idx]
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec /= norm
            cosine_sim = np.dot(self.tfidf_dense, query_vec)
            
        # Kết hợp độ tương đồng với điểm Bayesian Weighted Rating
        norm_wr = self.df["norm_wr"].values
        composite_scores = 0.80 * cosine_sim + 0.20 * norm_wr
        similar_indices = composite_scores.argsort()[::-1]
        
        results = []
        seen_titles = set()
        for i in similar_indices:
            raw_sim = float(cosine_sim[i])
            if raw_sim <= 0.001 and len(results) >= 5:
                break
                
            movie_info = self.df.iloc[i].to_dict()
            m_title = movie_info.get("title", "").strip().lower()
            if m_title in seen_titles:
                continue
            seen_titles.add(m_title)
            
            movie_info["similarity_score"] = round(raw_sim, 4)
            movie_info["composite_score"] = round(float(composite_scores[i]), 4)
            
            # Tạo lý do gợi ý cho tìm kiếm theo cốt truyện
            tgt_genres = [g.strip() for g in str(movie_info.get("genres", "")).split(",") if g.strip() and g.strip().lower() != "unknown"]
            matched_genres = [g for g in tgt_genres if g.lower() in cleaned_query]
            if matched_genres:
                movie_info["recommendation_reason"] = f"Khớp thể loại {', '.join(matched_genres)} và chủ đề cốt truyện tìm kiếm."
            else:
                movie_info["recommendation_reason"] = f"Khớp {(raw_sim * 100):.0f}% với mô tả nội dung bạn đang tìm kiếm."
                
            results.append(movie_info)
            if len(results) >= top_n:
                break
                
        return results
