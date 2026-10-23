# -*- coding: utf-8 -*-
"""
Bộ kiểm thử tính năng Quản lý Lịch sử xem phim và Đánh giá (History & Rating Tests).
Kiểm tra: Thêm, đọc, cập nhật, xóa lịch sử/đánh giá, và bảo mật phân quyền (chống IDOR).
"""

import pytest
from fastapi import status


# ----------------------------------------------------------------------
# 1. KIỂM THỬ LỊCH SỬ XEM PHIM (WATCH HISTORY)
# ----------------------------------------------------------------------

def test_add_and_get_watch_history(client, auth_headers):
    # Kiểm tra ghi nhận phim đã xem và truy vấn lịch sử
    payload = {
        "movie_id": "tt0816692",
        "movie_title": "Interstellar",
        "poster_url": "https://example.com/interstellar.jpg"
    }
    response = client.post("/api/history", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["movie_id"] == "tt0816692"
    assert data["movie_title"] == "Interstellar"

    # Lấy danh sách lịch sử
    get_res = client.get("/api/history", headers=auth_headers)
    assert get_res.status_code == status.HTTP_200_OK
    history_list = get_res.json()
    assert len(history_list) >= 1
    assert any(item["movie_id"] == "tt0816692" for item in history_list)


def test_delete_single_history_item(client, auth_headers):
    # Kiểm tra xóa 1 bộ phim cụ thể khỏi lịch sử xem
    client.post("/api/history", json={"movie_id": "tt0468569", "movie_title": "The Dark Knight"}, headers=auth_headers)

    # Xóa phim tt0468569
    del_res = client.delete("/api/history/tt0468569", headers=auth_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert "đã xóa phim khỏi lịch sử" in del_res.json()["message"].lower()

    # Xác nhận phim không còn trong lịch sử
    get_res = client.get("/api/history", headers=auth_headers)
    assert not any(item["movie_id"] == "tt0468569" for item in get_res.json())


def test_clear_all_history(client, auth_headers):
    # Kiểm tra tính năng xóa toàn bộ lịch sử xem phim
    client.post("/api/history", json={"movie_id": "tt1375666", "movie_title": "Inception"}, headers=auth_headers)
    client.post("/api/history", json={"movie_id": "tt0137523", "movie_title": "Fight Club"}, headers=auth_headers)

    # Xóa tất cả
    clear_res = client.delete("/api/history", headers=auth_headers)
    assert clear_res.status_code == status.HTTP_200_OK

    # Xác nhận danh sách lịch sử rỗng
    get_res = client.get("/api/history", headers=auth_headers)
    assert len(get_res.json()) == 0


def test_history_idor_isolation(client, auth_headers, auth_headers_user2):
    # Kiểm tra bảo mật IDOR: Người dùng 2 không thể xem hoặc xóa lịch sử của người dùng 1
    # User 1 thêm phim
    client.post("/api/history", json={"movie_id": "tt0111161", "movie_title": "The Shawshank Redemption"}, headers=auth_headers)

    # User 2 truy vấn lịch sử -> Không thấy phim của User 1
    user2_get = client.get("/api/history", headers=auth_headers_user2)
    assert not any(item["movie_id"] == "tt0111161" for item in user2_get.json())

    # User 2 cố gắng xóa phim mà mình chưa từng xem -> Phải nhận 404
    user2_del = client.delete("/api/history/tt0111161", headers=auth_headers_user2)
    assert user2_del.status_code == status.HTTP_404_NOT_FOUND

    # Xác nhận lịch sử của User 1 vẫn an toàn nguyên vẹn
    user1_get = client.get("/api/history", headers=auth_headers)
    assert any(item["movie_id"] == "tt0111161" for item in user1_get.json())


# ----------------------------------------------------------------------
# 2. KIỂM THỬ ĐÁNH GIÁ PHIM (RATINGS)
# ----------------------------------------------------------------------

def test_add_and_update_rating(client, auth_headers):
    # Kiểm tra gửi đánh giá sao và cập nhật lại điểm đánh giá
    payload = {
        "movie_id": "tt0816692",
        "movie_title": "Interstellar",
        "score": 9.5,
        "comment": "Tuyệt phẩm khoa học viễn tưởng"
    }
    res = client.post("/api/ratings", json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["score"] == 9.5

    # Cập nhật lại số điểm cho cùng một phim
    update_payload = {
        "movie_id": "tt0816692",
        "movie_title": "Interstellar",
        "score": 10.0,
        "comment": "Kiệt tác vượt thời gian!"
    }
    update_res = client.post("/api/ratings", json=update_payload, headers=auth_headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["score"] == 10.0
    assert update_res.json()["comment"] == "Kiệt tác vượt thời gian!"


def test_delete_rating(client, auth_headers):
    # Kiểm tra xóa đánh giá của người dùng
    client.post("/api/ratings", json={"movie_id": "tt0137523", "score": 8.5}, headers=auth_headers)

    # Xóa đánh giá
    del_res = client.delete("/api/ratings/tt0137523", headers=auth_headers)
    assert del_res.status_code == status.HTTP_200_OK

    # Lấy lại đánh giá của phim này -> Phải trả về None vì không còn tồn tại
    get_res = client.get("/api/ratings/tt0137523", headers=auth_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json() is None


def test_rating_score_validation(client, auth_headers):
    # Kiểm tra ràng buộc validation điểm số (phải từ 1.0 đến 10.0)
    # Điểm nhỏ hơn 1.0 -> 422 Unprocessable Entity
    invalid_low = {"movie_id": "tt0816692", "score": 0.0}
    res_low = client.post("/api/ratings", json=invalid_low, headers=auth_headers)
    assert res_low.status_code == 422

    # Điểm lớn hơn 10.0 -> 422 Unprocessable Entity
    invalid_high = {"movie_id": "tt0816692", "score": 10.5}
    res_high = client.post("/api/ratings", json=invalid_high, headers=auth_headers)
    assert res_high.status_code == 422


def test_ratings_idor_isolation(client, auth_headers, auth_headers_user2):
    # Kiểm tra bảo mật IDOR cho đánh giá: User 2 không thể xem hoặc xóa đánh giá của User 1
    client.post("/api/ratings", json={"movie_id": "tt1375666", "score": 9.0}, headers=auth_headers)

    # User 2 kiểm tra đánh giá phim đó của mình -> Trả về None vì User 2 chưa đánh giá
    user2_check = client.get("/api/ratings/tt1375666", headers=auth_headers_user2)
    assert user2_check.status_code == status.HTTP_200_OK
    assert user2_check.json() is None

    # User 2 cố gắng xóa đánh giá phim của User 1 -> 404 Not Found vì User 2 không sở hữu bản ghi đó
    user2_del = client.delete("/api/ratings/tt1375666", headers=auth_headers_user2)
    assert user2_del.status_code == status.HTTP_404_NOT_FOUND
