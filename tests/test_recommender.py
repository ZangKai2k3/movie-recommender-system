# -*- coding: utf-8 -*-
"""
Bộ kiểm thử thuật toán Gợi ý Phim (Recommender Algorithm Tests).
Kiểm tra: Content-Based Filtering TF-IDF, Cosine Similarity, Hybrid Bayesian Ranking,
lý do gợi ý minh bạch (Explainable AI), khử trùng lặp và xử lý ngoại lệ.
"""

import pytest
from src.config import DATA_PATH
from src.recommender.content_based import ContentBasedRecommender


@pytest.fixture(scope="module")
def recommender():
    """Khởi tạo một instance ContentBasedRecommender dùng chung cho toàn module test."""
    return ContentBasedRecommender(dataset_path=DATA_PATH)


def test_recommender_initialization(recommender):
    # Kiểm tra khởi tạo thành công và dữ liệu được nạp vào bộ nhớ
    assert recommender.df is not None
    assert len(recommender.df) > 0
    assert "norm_wr" in recommender.df.columns
    assert recommender.indices is not None


def test_recommend_by_title_returns_expected_results(recommender):
    # Kiểm tra gợi ý phim theo tên (ví dụ: Inception)
    results = recommender.recommend("Inception", top_n=5)
    
    assert len(results) == 5
    # Đảm bảo phim gốc không nằm trong danh sách gợi ý
    titles = [m["title"].lower() for m in results]
    assert "inception" not in titles
    
    # Kiểm tra các trường dữ liệu quan trọng
    first = results[0]
    assert "title" in first
    assert "genres" in first
    assert "similarity_score" in first
    assert "composite_score" in first
    assert "recommendation_reason" in first
    assert isinstance(first["recommendation_reason"], str)
    assert len(first["recommendation_reason"]) > 0


def test_recommend_ranking_order(recommender):
    # Kiểm tra kết quả được sắp xếp giảm dần theo composite_score
    results = recommender.recommend("The Dark Knight", top_n=5)
    scores = [m["composite_score"] for m in results]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], "Danh sách phải được sắp xếp theo composite_score giảm dần"


def test_recommend_deduplication(recommender):
    # Kiểm tra tính năng khử trùng lặp kết quả
    results = recommender.recommend("Interstellar", top_n=10)
    seen_titles = set()
    for item in results:
        t = item["title"].strip().lower()
        assert t not in seen_titles, f"Phát hiện phim bị trùng lặp: {t}"
        seen_titles.add(t)


def test_recommend_case_insensitive(recommender):
    # Kiểm tra tra cứu không phân biệt hoa thường và khoảng trắng
    results_upper = recommender.recommend("THE DARK KNIGHT", top_n=3)
    results_lower = recommender.recommend("the dark knight", top_n=3)
    
    assert [m["title"] for m in results_upper] == [m["title"] for m in results_lower]


def test_recommend_nonexistent_movie_raises_error(recommender):
    # Kiểm tra bắt lỗi khi tìm kiếm phim không tồn tại
    with pytest.raises(ValueError, match="Không tìm thấy phim"):
        recommender.recommend("NonExistentMovieTitle999999")


def test_recommend_empty_movie_raises_error(recommender):
    # Kiểm tra bắt lỗi khi tên phim rỗng hoặc toàn khoảng trắng
    with pytest.raises(ValueError, match="Vui lòng nhập tên phim"):
        recommender.recommend("")
        
    with pytest.raises(ValueError, match="Vui lòng nhập tên phim"):
        recommender.recommend("   ")


def test_recommend_by_text(recommender):
    # Kiểm tra tìm kiếm gợi ý bằng đoạn văn cốt truyện tự do
    query = "astronauts deep space exploration gravity black hole"
    results = recommender.recommend_by_text(query, top_n=5)
    
    assert len(results) > 0
    assert len(results) <= 5
    for m in results:
        assert "similarity_score" in m
        assert "composite_score" in m
        assert "recommendation_reason" in m
        assert len(m["recommendation_reason"]) > 0


def test_recommend_by_text_empty(recommender):
    # Kiểm tra truy vấn rỗng trả về danh sách rỗng an toàn
    assert recommender.recommend_by_text("") == []
    assert recommender.recommend_by_text("   ") == []


def test_generate_recommendation_reason_logic(recommender):
    # Kiểm tra logic tạo lý do gợi ý minh bạch (Explainable AI)
    # Trường hợp 1: Có cả thể loại chung và diễn viên chung
    src1 = {"title": "Movie A", "genres": "Action, Sci-Fi", "cast": "Tom Hardy, Leonardo DiCaprio"}
    tgt1 = {"title": "Movie B", "genres": "Action, Thriller", "cast": "Leonardo DiCaprio, Cillian Murphy"}
    reason1 = recommender._generate_recommendation_reason(src1, tgt1, 0.85)
    assert "thể loại" in reason1.lower()
    assert "Leonardo Dicaprio" in reason1

    # Trường hợp 2: Chỉ có thể loại chung
    src2 = {"title": "Movie A", "genres": "Animation, Adventure", "cast": "Actor 1"}
    tgt2 = {"title": "Movie B", "genres": "Animation, Family", "cast": "Actor 2"}
    reason2 = recommender._generate_recommendation_reason(src2, tgt2, 0.70)
    assert "thể loại" in reason2.lower()
    assert "Animation" in reason2

    # Trường hợp 3: Không có gì chung ngoài cốt truyện
    src3 = {"title": "Movie A", "genres": "Drama", "cast": "Actor 1"}
    tgt3 = {"title": "Movie B", "genres": "Comedy", "cast": "Actor 2"}
    reason3 = recommender._generate_recommendation_reason(src3, tgt3, 0.65)
    assert "tương đồng về chủ đề cốt truyện" in reason3.lower() or "65%" in reason3

