# -*- coding: utf-8 -*-
"""
Router cung cấp các API endpoint về Dữ liệu Phim và Gợi ý Phim:
- Lấy danh sách phim phổ biến / Lọc theo thể loại: GET /api/movies
- Lấy danh sách toàn bộ thể loại phim (Genres): GET /api/movies/genres
- Gợi ý phim theo tên phim: GET /api/movies/recommendations?movie=...
- Gợi ý phim theo mô tả cốt truyện tự do: GET /api/movies/recommend-by-plot?query=...
- Gợi ý phim cá nhân hóa cho người dùng đăng nhập: GET /api/movies/personalized
"""

import os
import urllib.parse
import urllib.request
import json
from collections import Counter
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd

from ..config import DATA_PATH
from ..database.connection import get_db
from ..database.models import User, WatchHistory, Rating
from ..auth.dependencies import get_current_user
from ..recommender.content_based import ContentBasedRecommender

router = APIRouter(prefix="/api/movies", tags=["Phim và Gợi ý (Movies & Recommendations)"])

_recommender: Optional[ContentBasedRecommender] = None
_movies_df: Optional[pd.DataFrame] = None

def get_recommender_and_data():
    """Tải và lưu đệm (cache) mô hình gợi ý cùng DataFrame phim vào bộ nhớ."""
    global _recommender, _movies_df
    if _movies_df is None and os.path.exists(DATA_PATH):
        _movies_df = pd.read_csv(DATA_PATH).fillna("")
    if _recommender is None and os.path.exists(DATA_PATH):
        _recommender = ContentBasedRecommender(DATA_PATH)
    return _recommender, _movies_df

def enrich_movie_with_media_links(movie_dict: dict) -> dict:
    """Tự động bổ sung các đường dẫn xem trực tuyến và trailer vào dữ liệu phim."""
    clean_dict = {}
    for k, v in movie_dict.items():
        if isinstance(v, float) and (v != v):  # Kiểm tra math.isnan
            clean_dict[k] = ""
        else:
            clean_dict[k] = v
            
    mid = clean_dict.get("id", "")
    title = clean_dict.get("title", "")
    
    # 1. Các nguồn phát trực tuyến ổn định không chứa mã độc hại
    clean_dict["watch_url"] = f"https://2embed.cc/embed/{mid}"
    clean_dict["watch_url_backup"] = f"https://www.2embed.skin/embed/{mid}"
    clean_dict["watch_url_server3"] = f"https://multiembed.mov/?video_id={mid}"
    
    # 2. Đường dẫn mở trailer chính thức trên YouTube và trang IMDb gốc
    clean_dict["trailer_url"] = f"https://www.youtube.com/results?search_query={urllib.parse.quote(title)}+official+trailer"
    clean_dict["imdb_url"] = f"https://www.imdb.com/title/{mid}/"
    return clean_dict

@router.get("/genres", summary="Lấy danh sách các thể loại phim kèm số lượng phim")
def get_genres():
    """Trích xuất danh sách tất cả các tag thể loại có trong tập dữ liệu phim."""
    _, df = get_recommender_and_data()
    if df is None or df.empty:
        return []
        
    genre_counter = Counter()
    for item in df["genres"].dropna():
        if isinstance(item, str):
            genres = [g.strip() for g in item.split(",") if g.strip() and g.strip().lower() != "unknown"]
            genre_counter.update(genres)
            
    # Sắp xếp các thể loại có nhiều phim nhất lên đầu
    sorted_genres = [
        {"name": name, "count": count}
        for name, count in genre_counter.most_common()
    ]
    return sorted_genres

@router.get("", summary="Lấy danh sách các phim thịnh hành (hỗ trợ lọc theo thể loại & tìm kiếm)")
def list_movies(
    page: int = Query(1, ge=1, description="Số trang"),
    limit: int = Query(24, ge=1, le=100, description="Số phim mỗi trang"),
    genre: Optional[str] = Query(None, description="Lọc theo thể loại (ví dụ: Action, Sci-Fi, Drama)"),
    search: Optional[str] = Query(None, description="Từ khóa tìm kiếm theo tên phim")
):
    """Lấy danh sách phim có phân trang, hỗ trợ lọc theo thể loại và tìm kiếm từ khóa."""
    _, df = get_recommender_and_data()
    if df is None or df.empty:
        return {"total": 0, "page": page, "limit": limit, "items": []}
        
    filtered = df
    if genre and genre.strip().lower() not in ("all", "tat ca", "tất cả"):
        g_lower = genre.strip().lower()
        filtered = filtered[filtered["genres"].str.lower().str.contains(g_lower, na=False)]
        
    if search and search.strip():
        s_lower = search.strip().lower()
        filtered = filtered[filtered["title"].str.lower().str.contains(s_lower, na=False)]
        
    total = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    raw_items = filtered.iloc[start_idx:end_idx].to_dict(orient="records")
    items = [enrich_movie_with_media_links(m) for m in raw_items]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "selected_genre": genre,
        "items": items
    }

@router.get("/recommendations", summary="Gợi ý phim dựa trên một bộ phim đã chọn")
def get_recommendations(
    movie: str = Query(..., description="Tên phim bạn yêu thích (ví dụ: Inception, The Dark Knight)"),
    top_n: int = Query(10, ge=1, le=50, description="Số lượng gợi ý muốn nhận")
):
    """Gợi ý các phim tương đồng với phim đã chọn bằng TF-IDF + Cosine Similarity kèm lý do minh bạch."""
    recommender, _ = get_recommender_and_data()
    if recommender is None:
        raise HTTPException(status_code=500, detail="Mô hình gợi ý chưa sẵn sàng. Hãy kiểm tra file dữ liệu.")
        
    try:
        results = recommender.recommend(movie, top_n=top_n)
        enriched_results = [enrich_movie_with_media_links(m) for m in results]
        return {
            "query_movie": movie,
            "count": len(enriched_results),
            "recommendations": enriched_results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

def auto_translate_to_english(text: str) -> str:
    """
    Tự động phát hiện và dịch câu truy vấn từ Tiếng Việt sang Tiếng Anh.
    Giúp người dùng có thể nhập mô tả bằng Tiếng Việt mà hệ thống vẫn tìm kiếm chính xác
    trên tập dữ liệu cốt truyện phim bằng Tiếng Anh.
    """
    if not text or not text.strip():
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = "".join([item[0] for item in data[0] if item and item[0]])
            if translated:
                return translated
    except Exception:
        pass
    return text

@router.get("/recommend-by-plot", summary="Gợi ý phim dựa trên đoạn miêu tả cốt truyện tự do của người dùng")
def recommend_by_plot(
    query: str = Query(..., description="Đoạn miêu tả nội dung phim bạn muốn xem (hỗ trợ cả Tiếng Việt và Tiếng Anh)"),
    top_n: int = Query(10, ge=1, le=50, description="Số lượng phim gợi ý trả về")
):
    """
    Thuật toán NLP hỗ trợ đa ngôn ngữ:
    Tự động dịch câu mô tả tiếng Việt sang tiếng Anh nếu cần, sau đó vector hóa TF-IDF
    và tính độ tương đồng cosin với tóm tắt cốt truyện phim để tìm phim khớp nhất.
    """
    recommender, _ = get_recommender_and_data()
    if recommender is None:
        raise HTTPException(status_code=500, detail="Mô hình gợi ý chưa sẵn sàng.")
        
    english_query = auto_translate_to_english(query)
    results = recommender.recommend_by_text(english_query, top_n=top_n)
    enriched_results = [enrich_movie_with_media_links(m) for m in results]
    
    return {
        "original_query": query,
        "translated_query": english_query,
        "count": len(enriched_results),
        "recommendations": enriched_results
    }

@router.get("/personalized", summary="Gợi ý phim cá nhân hóa dựa trên lịch sử xem và đánh giá của User")
def get_personalized_recommendations(
    top_n: int = Query(12, ge=1, le=50, description="Số lượng gợi ý muốn nhận"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Thuật toán Gợi Ý Cá Nhân Hóa (Personalized Recommendation):
    1. Lấy toàn bộ phim user đã xem trong watch_history và các phim user đánh giá cao (score >= 6.0) trong ratings.
    2. Tổng hợp gu sở thích (User Preference Profile) từ các thể loại, diễn viên và cốt truyện mà user quan tâm.
    3. Tìm các phim tương tự nhất trên kho phim bằng TF-IDF & Cosine Similarity.
    4. Tự động loại bỏ các phim mà user đã xem rồi và các phim user chê (< 5.0 sao).
    5. Đính kèm lý do gợi ý minh bạch cho từng phim.
    """
    recommender, df = get_recommender_and_data()
    if recommender is None or df is None:
        raise HTTPException(status_code=500, detail="Mô hình gợi ý chưa sẵn sàng.")
        
    # 1. Truy vấn lịch sử xem và đánh giá của user hiện tại
    watched_records = db.query(WatchHistory).filter(WatchHistory.user_id == current_user.id).all()
    watched_ids = {h.movie_id for h in watched_records}
    
    rated_records = db.query(Rating).filter(Rating.user_id == current_user.id).all()
    liked_ids = {r.movie_id for r in rated_records if r.score >= 6.0}
    disliked_ids = {r.movie_id for r in rated_records if r.score < 5.0}
    
    # 2. Xử lý trường hợp người dùng mới (Cold-Start Problem): Chưa xem hoặc chấm điểm phim nào
    favorite_movie_ids = list(watched_ids.union(liked_ids))
    if not favorite_movie_ids:
        # Gợi ý top phim có điểm xếp hạng Bayesian Weighted Rating cao nhất toàn hệ thống
        top_popular = df.sort_values(by="weighted_rating", ascending=False).head(top_n).to_dict(orient="records")
        for m in top_popular:
            m["recommendation_reason"] = "Top phim kinh điển có điểm đánh giá xuất sắc nhất toàn cầu."
        return {
            "mode": "cold_start",
            "count": len(top_popular),
            "message": "Bạn chưa có lịch sử xem phim. Đây là các bộ phim kinh điển được đánh giá cao nhất dành cho bạn.",
            "recommendations": [enrich_movie_with_media_links(m) for m in top_popular]
        }
        
    # 3. Xây dựng User Preference Profile (Gom đặc trưng các phim user đã tương tác tích cực)
    user_movies_df = df[df["id"].isin(favorite_movie_ids)]
    
    # Thống kê top thể loại mà người dùng xem nhiều nhất để đưa vào lý do gợi ý
    user_genres_counter = Counter()
    profile_features = []
    for _, row in user_movies_df.iterrows():
        genres_str = str(row.get("genres", ""))
        for g in genres_str.split(","):
            g_clean = g.strip()
            if g_clean and g_clean.lower() != "unknown":
                user_genres_counter[g_clean] += 1
        profile_features.append(f"{row.get('genres', '')} {row.get('cast', '')} {row.get('plot_clean', '')[:300]}")
        
    top_user_genres = [g for g, _ in user_genres_counter.most_common(3)]
    user_profile_text = " ".join(profile_features)
    
    # 4. Gợi ý phim dựa trên User Profile
    candidate_movies = recommender.recommend_by_text(
        user_profile_text,
        top_n=top_n + len(watched_ids) + len(disliked_ids) + 20
    )
    
    # 5. Lọc bỏ các phim user ĐÃ XEM RỒI và các phim user KHÔNG THÍCH (< 5 sao)
    filtered_recommendations = []
    seen_ids = set()
    
    for m in candidate_movies:
        mid = m.get("id")
        if mid in seen_ids:
            continue
        seen_ids.add(mid)
        
        if mid not in watched_ids and mid not in disliked_ids:
            # Gán lý do gợi ý minh bạch dựa trên thể loại ưa thích
            candidate_genres = {g.strip().lower() for g in str(m.get("genres", "")).split(",") if g.strip()}
            matched = [g for g in top_user_genres if g.lower() in candidate_genres]
            if matched:
                m["recommendation_reason"] = f"Phù hợp với gu thể loại {', '.join(matched)} từ các phim bạn đã thích."
            else:
                m["recommendation_reason"] = "Được đề xuất dựa trên phong cách các bộ phim bạn đã xem gần đây."
                
            filtered_recommendations.append(enrich_movie_with_media_links(m))
            if len(filtered_recommendations) >= top_n:
                break
                
    genres_msg = f" (Thể loại ưa thích: {', '.join(top_user_genres)})" if top_user_genres else ""
    return {
        "mode": "personalized",
        "user": current_user.username,
        "total_watched": len(watched_ids),
        "total_rated": len(rated_records),
        "count": len(filtered_recommendations),
        "message": f"Gợi ý cá nhân hóa cho {current_user.username} dựa trên {len(watched_ids)} phim đã xem{genres_msg}.",
        "recommendations": filtered_recommendations
    }
