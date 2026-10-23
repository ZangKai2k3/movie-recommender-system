# -*- coding: utf-8 -*-
"""
Bộ kiểm thử API Phim và Gợi ý Phim (Movies & Recommender API Endpoints Tests).
Kiểm tra: Danh sách phim, lọc thể loại, tìm kiếm, gợi ý theo phim, gợi ý theo cốt truyện,
và gợi ý cá nhân hóa (Personalized Recommendations).
"""

import pytest
from fastapi import status


def test_get_genres(client):
    # Kiểm tra API danh sách thể loại phim
    response = client.get("/api/movies/genres")
    assert response.status_code == status.HTTP_200_OK
    genres = response.json()
    assert isinstance(genres, list)
    assert len(genres) > 0
    assert "name" in genres[0]
    assert "count" in genres[0]


def test_list_movies_pagination(client):
    # Kiểm tra phân trang danh sách phim
    response = client.get("/api/movies?page=1&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["items"]) == 10
    assert data["total"] > 10


def test_list_movies_filter_by_genre(client):
    # Kiểm tra lọc phim theo thể loại Action
    response = client.get("/api/movies?genre=Action&limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) > 0
    for movie in data["items"]:
        assert "action" in movie["genres"].lower()


def test_list_movies_search_by_title(client):
    # Kiểm tra tìm kiếm phim theo từ khóa tên phim
    response = client.get("/api/movies?search=Dark Knight")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) > 0
    assert any("dark knight" in m["title"].lower() for m in data["items"])


def test_get_recommendations_success(client):
    # Kiểm tra gợi ý phim dựa trên tên phim có sẵn
    response = client.get("/api/movies/recommendations?movie=Inception&top_n=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["query_movie"] == "Inception"
    assert data["count"] == 5
    assert len(data["recommendations"]) == 5
    for item in data["recommendations"]:
        assert "recommendation_reason" in item
        assert "watch_url" in item


def test_get_recommendations_movie_not_found(client):
    # Kiểm tra trả về lỗi 404 khi phim không có trong dữ liệu
    response = client.get("/api/movies/recommendations?movie=NonExistentMovieAbc123")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_recommend_by_plot(client):
    # Kiểm tra gợi ý phim bằng đoạn mô tả cốt truyện
    response = client.get("/api/movies/recommend-by-plot?query=space exploration astronauts&top_n=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] > 0
    assert len(data["recommendations"]) <= 5
    first = data["recommendations"][0]
    assert "recommendation_reason" in first
    assert "watch_url" in first


def test_personalized_recommendations_cold_start(client, auth_headers):
    # Kiểm tra gợi ý cá nhân hóa cho người dùng mới (Cold Start - chưa xem, chưa đánh giá)
    response = client.get("/api/movies/personalized?top_n=6", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 6
    assert len(data["recommendations"]) == 6
    assert "kinh điển" in data["message"].lower() or "cold_start" in data["mode"].lower()


def test_personalized_recommendations_with_history(client, auth_headers):
    # Kiểm tra gợi ý cá nhân hóa sau khi người dùng đã xem một số phim
    # Người dùng xem Interstellar (Sci-Fi, Adventure)
    client.post("/api/history", json={"movie_id": "tt0816692", "movie_title": "Interstellar"}, headers=auth_headers)

    response = client.get("/api/movies/personalized?top_n=6", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["recommendations"]) == 6
    # Phim đã xem (Interstellar) không được xuất hiện lại trong kết quả gợi ý cá nhân hóa
    rec_ids = [m.get("id") for m in data["recommendations"]]
    assert "tt0816692" not in rec_ids


def test_personalized_recommendations_unauthorized(client):
    # Kiểm tra yêu cầu đăng nhập đối với route cá nhân hóa
    response = client.get("/api/movies/personalized")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
