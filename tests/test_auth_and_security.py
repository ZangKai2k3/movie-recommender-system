# -*- coding: utf-8 -*-
"""
Bộ kiểm thử chức năng Xác thực và Bảo mật (Authentication & Security Tests).
Kiểm tra: Đăng ký, đăng nhập, cấp phát JWT, xác thực token, chống truy cập trái phép.
"""

import pytest
from fastapi import status


def test_register_success(client):
    # Kiểm tra đăng ký tài khoản mới thành công
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # Đảm bảo không lộ hash mật khẩu


def test_register_duplicate_username(client, test_user):
    # Kiểm tra đăng ký thất bại khi trùng tên đăng nhập
    payload = {
        "username": test_user.username,
        "email": "another@example.com",
        "password": "Password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "đã được sử dụng" in response.json()["detail"].lower()


def test_register_duplicate_email(client, test_user):
    # Kiểm tra đăng ký thất bại khi trùng email
    payload = {
        "username": "unique_username",
        "email": test_user.email,
        "password": "Password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()["detail"].lower()
    assert "đã được đăng ký" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    # Kiểm tra đăng nhập thành công với tài khoản và mật khẩu chính xác
    payload = {
        "username": test_user.username,
        "password": "Password123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == test_user.username


def test_login_invalid_password(client, test_user):
    # Kiểm tra đăng nhập thất bại khi sai mật khẩu
    payload = {
        "username": test_user.username,
        "password": "WrongPassword999"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_nonexistent_user(client):
    # Kiểm tra đăng nhập thất bại khi tài khoản không tồn tại
    payload = {
        "username": "nonexistent_user_99",
        "password": "Password123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_profile(client, auth_headers, test_user):
    # Kiểm tra lấy thông tin cá nhân của người dùng đã xác thực
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_protected_route_unauthorized_without_token(client):
    # Kiểm tra bảo vệ route yêu cầu đăng nhập: từ chối khi không có token
    response = client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_route_with_invalid_token(client):
    # Kiểm tra bảo vệ route khi gửi kèm token không hợp lệ hoặc giả mạo
    headers = {"Authorization": "Bearer invalid_malformed_token_string"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
