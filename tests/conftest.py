# -*- coding: utf-8 -*-
"""
Fixtures dùng chung cho toàn bộ bài kiểm thử (Test Fixtures).
Khởi tạo cơ sở dữ liệu SQLite in-memory độc lập cho quá trình test.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database.connection import Base, get_db
from src.auth.security import hash_password, create_access_token
from src.database.models import User

# Sử dụng SQLite in-memory độc lập cho môi trường kiểm thử
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Tạo các bảng cơ sở dữ liệu trước khi chạy toàn bộ test và hủy sau khi hoàn thành."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Cung cấp session cơ sở dữ liệu sạch cho từng bài test độc lập."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Cung cấp TestClient của FastAPI với database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Tạo người dùng mẫu 1 phục vụ kiểm thử."""
    user = User(
        username="testuser1",
        email="testuser1@example.com",
        hashed_password=hash_password("Password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user2(db_session):
    """Tạo người dùng mẫu 2 phục vụ kiểm thử phân quyền và chống IDOR."""
    user = User(
        username="testuser2",
        email="testuser2@example.com",
        hashed_password=hash_password("Password456")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Tạo Authorization Bearer header cho test_user."""
    token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_user2(test_user2):
    """Tạo Authorization Bearer header cho test_user2."""
    token = create_access_token({"sub": test_user2.username, "user_id": test_user2.id})
    return {"Authorization": f"Bearer {token}"}

