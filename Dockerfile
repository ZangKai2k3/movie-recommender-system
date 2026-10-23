# ==========================================
# Dockerfile cho Backend FastAPI (HTGoiYPhim)
# ==========================================
FROM python:3.11-slim

# Thiết lập môi trường
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Cài đặt các gói hệ thống cần thiết (nếu có biên dịch C cho bcrypt/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY src/ ./src/
COPY data/ ./data/
COPY run_server.py .
COPY run_crawler.py .
COPY recommend.py .

# Tạo sẵn các thư mục cần thiết
RUN mkdir -p data/processed data/raw logs

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Khởi chạy FastAPI thông qua Uvicorn server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

