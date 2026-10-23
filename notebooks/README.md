# 📚 QUY TRÌNH NOTEBOOKS - HỆ THỐNG GỢI Ý PHIM (IMDb 2000 - 2026)

Bộ Notebook này được chia thành **4 giai đoạn tuần tự** (chuẩn quy trình Khoa học Dữ liệu / Đồ án):

```
notebooks/
├── 01_Crawl_IMDb_Data.ipynb                      (Phần 1: Cào 20.000 phim IMDb giai đoạn 2000 - 2026)
├── 02_Data_Cleaning_And_Type_Casting.ipynb       (Phần 2: Ép kiểu dữ liệu, xử lý thiếu \N, làm sạch thể loại)
├── 03_Exploratory_Data_Analysis.ipynb            (Phần 3: Thống kê mô tả, phân tích & trực quan hóa biểu đồ)
└── 04_Feature_Engineering_And_Recommendation.ipynb (Phần 4: Bayesian Weighted Rating, TF-IDF, Cosine Similarity)
```

---

## 🚀 Hướng Dẫn Chạy Tuần Tự

### 1️⃣ Phần 1: [`01_Crawl_IMDb_Data.ipynb`](file:///d:/HTGoiYPhim/notebooks/01_Crawl_IMDb_Data.ipynb)
* **Nhiệm vụ**: Kết nối HTTP luồng IMDb nén `.tsv.gz`, lọc đúng 20.000 phim điện ảnh phát hành từ năm 2000 đến 2026.
* **Đầu ra**: `data/raw/raw_movies_2000_2026.csv` và `.json`.

### 2️⃣ Phần 2: [`02_Data_Cleaning_And_Type_Casting.ipynb`](file:///d:/HTGoiYPhim/notebooks/02_Data_Cleaning_And_Type_Casting.ipynb)
* **Nhiệm vụ**: Đọc dữ liệu thô từ Phần 1, kiểm tra missing values, ép kiểu dữ liệu:
  - `year`: int32
  - `runtime_minutes`: int32 (điền median cho các phim thiếu thời lượng)
  - `rating`: float64
  - `votes`: int64
  - `genres`: mảng `genres_list` và chuỗi `genres_clean`
* **Đầu ra**: `data/interim/cleaned_movies_2000_2026.csv` và `.json`.

### 3️⃣ Phần 3: [`03_Exploratory_Data_Analysis.ipynb`](file:///d:/HTGoiYPhim/notebooks/03_Exploratory_Data_Analysis.ipynb)
* **Nhiệm vụ**: Phân tích thống kê mô tả (Mean, Min, Max), vẽ biểu đồ:
  - Biểu đồ phân bố số phim qua các năm (2000 - 2026).
  - Biểu đồ phân bố điểm rating (Histogram).
  - Biểu đồ Top 15 thể loại xuất hiện nhiều nhất (Barh).
  - Top 10 phim nhiều lượt vote nhất.

### 4️⃣ Phần 4: [`04_Feature_Engineering_And_Recommendation.ipynb`](file:///d:/HTGoiYPhim/notebooks/04_Feature_Engineering_And_Recommendation.ipynb)
* **Nhiệm vụ**:
  - Tính điểm xếp hạng có trọng số Bayesian Weighted Rating (WR) chuẩn IMDb.
  - Xây dựng ma trận TF-IDF (`max_features=5000`) và hàm tính `cosine_similarity`.
  - Thử nghiệm gợi ý phim tương tự khi nhập tên phim (ví dụ: *Inception*, *The Dark Knight*).
  - Xuất dữ liệu hoàn chỉnh để nạp vào Backend FastAPI và Web App.
* **Đầu ra cuối cùng**: `data/processed/movies_20000_2000_2026.csv` và `.json`.

