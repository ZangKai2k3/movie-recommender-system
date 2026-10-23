# -*- coding: utf-8 -*-
"""
Script tự động tạo 4 file Jupyter Notebook chuyên biệt cho từng giai đoạn của Đồ án.
"""

import json
import os

os.makedirs("notebooks", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/interim", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

def make_nb(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

# ==============================================================================
# NOTEBOOK 1: CRAWL DỮ LIỆU IMDB
# ==============================================================================
nb1_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 🎬 PHẦN 1: THU THẬP DỮ LIỆU PHIM TỪ IMDB (2000 - 2026)\n",
            "## File: `01_Crawl_IMDb_Data.ipynb`\n",
            "---\n",
            "**Mục tiêu của phần này:**\n",
            "1. Kết nối trực tiếp đến luồng dữ liệu mở chính thức của IMDb (`datasets.imdbws.com`).\n",
            "2. Thiết lập điều kiện lọc thu thập **20.000 bộ phim** phát hành trong giai đoạn **2000 - 2026**.\n",
            "3. Lọc phim điện ảnh (`movie`, `tvMovie`), loại bỏ phim người lớn (`isAdult == 0`), lọc vote tối thiểu `>= 100`.\n",
            "4. Đọc giải nén luồng mạng trực tiếp (Streaming HTTP) vào DataFrame `df_raw` mà không cần tải file lớn về ổ cứng.\n",
            "5. Lưu dữ liệu thô vào thư mục `data/raw/raw_movies_2000_2026.csv`."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Khai báo thư viện phục vụ cào dữ liệu\n",
            "Sử dụng `urllib.request` để gửi HTTP request, `gzip` để giải nén luồng bộ nhớ, và `pandas` để quản lý bảng."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import time\n",
            "import gzip\n",
            "import urllib.request\n",
            "import pandas as pd\n",
            "\n",
            "print('✅ Đã nạp thành công các thư viện cào dữ liệu!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Thiết lập các thông số lọc khi cào dữ liệu\n",
            "Cấu hình thu thập đúng **20.000 phim** thuộc các năm từ **2000 đến 2026**."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Tham số cấu hình\n",
            "TARGET_LIMIT = 20000        # Số lượng phim cần lấy\n",
            "START_YEAR = 2000           # Năm bắt đầu\n",
            "END_YEAR = 2026             # Năm kết thúc\n",
            "MIN_VOTES = 100             # Số lượt bình chọn tối thiểu\n",
            "\n",
            "ALLOWED_TITLE_TYPES = {'movie', 'tvMovie'}  # Phim điện ảnh / Phim truyện\n",
            "EXCLUDE_ADULT = True                         # Không lấy phim người lớn\n",
            "\n",
            "RATINGS_URL = 'https://datasets.imdbws.com/title.ratings.tsv.gz'\n",
            "BASICS_URL = 'https://datasets.imdbws.com/title.basics.tsv.gz'\n",
            "\n",
            "print(f'🎯 Mục tiêu: {TARGET_LIMIT:,} phim | Năm: {START_YEAR} - {END_YEAR} | Votes >= {MIN_VOTES:,}')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 3. Quét luồng Ratings lấy điểm đánh giá & xếp hạng độ phổ biến"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('⏳ [Bước 1/2] Đang quét luồng IMDb Ratings qua mạng HTTP...')\n",
            "t0 = time.time()\n",
            "\n",
            "req_ratings = urllib.request.Request(RATINGS_URL, headers={'User-Agent': 'Mozilla/5.0'})\n",
            "ratings = {}\n",
            "\n",
            "with urllib.request.urlopen(req_ratings, timeout=30) as response:\n",
            "    with gzip.GzipFile(fileobj=response) as gz_stream:\n",
            "        gz_stream.readline()  # Bỏ qua dòng tiêu đề: tconst, averageRating, numVotes\n",
            "        for line in gz_stream:\n",
            "            parts = line.decode('utf-8').strip().split('\\t')\n",
            "            if len(parts) == 3:\n",
            "                tconst = parts[0]\n",
            "                votes = int(parts[2])\n",
            "                if votes >= MIN_VOTES:\n",
            "                    avg_rating = float(parts[1])\n",
            "                    ratings[tconst] = (avg_rating, votes)\n",
            "\n",
            "print(f'-> Đã quét {len(ratings):,} phim đạt chuẩn >= {MIN_VOTES} votes trong {time.time() - t0:.2f} giây.')\n",
            "\n",
            "# Sắp xếp theo số lượt vote giảm dần và chọn tập ứng viên đệm (70.000 phim)\n",
            "sorted_ratings = sorted(ratings.items(), key=lambda x: x[1][1], reverse=True)\n",
            "candidate_ids = {item[0] for item in sorted_ratings[:70000]}\n",
            "print(f'-> Đã chọn ra tập ứng viên thịnh hành nhất: {len(candidate_ids):,} mã phim.')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Quét luồng Basics lọc phim theo năm (2000 - 2026) & thể loại"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print(f'⏳ [Bước 2/2] Đang quét luồng IMDb Basics lọc phim phát hành {START_YEAR} - {END_YEAR}...')\n",
            "t1 = time.time()\n",
            "\n",
            "req_basics = urllib.request.Request(BASICS_URL, headers={'User-Agent': 'Mozilla/5.0'})\n",
            "raw_movie_list = []\n",
            "\n",
            "with urllib.request.urlopen(req_basics, timeout=60) as response:\n",
            "    with gzip.GzipFile(fileobj=response) as gz_stream:\n",
            "        gz_stream.readline()  # Bỏ qua tiêu đề\n",
            "        for line in gz_stream:\n",
            "            parts = line.decode('utf-8').strip().split('\\t')\n",
            "            tconst = parts[0]\n",
            "            \n",
            "            # Chỉ kiểm tra nếu phim nằm trong tập ứng viên vote cao\n",
            "            if tconst in candidate_ids:\n",
            "                title_type = parts[1]\n",
            "                is_adult = parts[4]\n",
            "                year_str = parts[5]\n",
            "                \n",
            "                # ÁP DỤNG ĐIỀU KIỆN LỌC:\n",
            "                # 1. Thuộc loại phim điện ảnh\n",
            "                # 2. Không phải phim người lớn\n",
            "                # 3. Năm phát hành nằm trong khoảng 2000 - 2026\n",
            "                if title_type in ALLOWED_TITLE_TYPES and is_adult == '0' and year_str != r'\\N':\n",
            "                    year = int(year_str)\n",
            "                    if START_YEAR <= year <= END_YEAR:\n",
            "                        rating, votes = ratings[tconst]\n",
            "                        raw_movie_list.append({\n",
            "                            'id': tconst,\n",
            "                            'title': parts[2],\n",
            "                            'original_title': parts[3],\n",
            "                            'year': year,\n",
            "                            'runtime_minutes': parts[7],\n",
            "                            'genres': parts[8],\n",
            "                            'rating': rating,\n",
            "                            'votes': votes\n",
            "                        })\n",
            "\n",
            "print(f'-> Đã trích xuất {len(raw_movie_list):,} phim hợp lệ trong {time.time() - t1:.2f} giây.')\n",
            "\n",
            "# Sắp xếp lần cuối theo votes giảm dần và lấy đúng số lượng mục tiêu 20.000\n",
            "raw_movie_list.sort(key=lambda m: m['votes'], reverse=True)\n",
            "final_movies = raw_movie_list[:TARGET_LIMIT]\n",
            "\n",
            "# Tạo DataFrame thô\n",
            "df_raw = pd.DataFrame(final_movies)\n",
            "print(f'\\n🎉 Đã thu thập thành công {len(df_raw):,} bộ phim!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Quan sát dữ liệu thô vừa thu thập"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print(f'Kích thước dữ liệu thô: {df_raw.shape[0]:,} dòng x {df_raw.shape[1]} cột')\n",
            "display(df_raw.head(10))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 6. Lưu dữ liệu thô ra thư mục `data/raw/`\n",
            "Lưu lại để sử dụng cho **Notebook 2 (Tiền xử lý & Ép kiểu dữ liệu)**."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "output_dir = 'data/raw'\n",
            "os.makedirs(output_dir, exist_ok=True)\n",
            "\n",
            "csv_raw_path = os.path.join(output_dir, 'raw_movies_2000_2026.csv')\n",
            "json_raw_path = os.path.join(output_dir, 'raw_movies_2000_2026.json')\n",
            "\n",
            "df_raw.to_csv(csv_raw_path, index=False, encoding='utf-8-sig')\n",
            "df_raw.to_json(json_raw_path, orient='records', force_ascii=False, indent=2)\n",
            "\n",
            "print(f'✅ Đã lưu file thô CSV: {csv_raw_path} ({os.path.getsize(csv_raw_path)/1024/1024:.2f} MB)')\n",
            "print(f'✅ Đã lưu file thô JSON: {json_raw_path} ({os.path.getsize(json_raw_path)/1024/1024:.2f} MB)')\n",
            "print('\\n👉 BƯỚC TIẾP THEO: Hãy mở file `02_Data_Cleaning_And_Type_Casting.ipynb` để thực hiện ép kiểu và làm sạch dữ liệu!')"
        ]
    }
]

# ==============================================================================
# NOTEBOOK 2: TIỀN XỬ LÝ & ÉP KIỂU DỮ LIỆU
# ==============================================================================
nb2_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 🧹 PHẦN 2: TIỀN XỬ LÝ & ÉP KIỂU DỮ LIỆU (DATA CLEANING & TYPE CASTING)\n",
            "## File: `02_Data_Cleaning_And_Type_Casting.ipynb`\n",
            "---\n",
            "**Mục tiêu của phần này:**\n",
            "1. Đọc lại file dữ liệu thô `data/raw/raw_movies_2000_2026.csv` vừa cào ở Phần 1.\n",
            "2. Kiểm tra chi tiết cấu trúc bảng, kiểu dữ liệu hiện tại (`dtypes`), các giá trị khuyết thiếu và ký tự `\\N`.\n",
            "3. **Ép kiểu dữ liệu (Type Casting)**:\n",
            "   - `year`: chuỗi $\\rightarrow$ số nguyên `int32`.\n",
            "   - `runtime_minutes`: thay `\\N` bằng NaN, điền trung vị (`median`), ép kiểu `int32`.\n",
            "   - `rating`: ép kiểu `float64`.\n",
            "   - `votes`: ép kiểu `int64`.\n",
            "4. **Làm sạch thể loại (`genres`)**: thay `\\N` bằng `Unknown`, tách list thể loại `genres_list`.\n",
            "5. Bổ sung các trường liên kết phát phim `watch_url` và `imdb_url`.\n",
            "6. Lưu dữ liệu đã làm sạch vào `data/interim/cleaned_movies_2000_2026.csv`."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Khai báo thư viện & Đọc dữ liệu thô"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "\n",
            "# Cấu hình hiển thị bảng Pandas\n",
            "pd.set_option('display.max_columns', None)\n",
            "pd.set_option('display.max_rows', 20)\n",
            "\n",
            "# Đọc dữ liệu thô từ file cào ở Phần 1\n",
            "raw_path = 'data/raw/raw_movies_2000_2026.csv'\n",
            "df = pd.read_csv(raw_path)\n",
            "print(f'✅ Đã nạp thành công {len(df):,} dòng dữ liệu thô từ {raw_path}!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Kiểm tra cấu trúc & Phát hiện vấn đề về kiểu dữ liệu (Data Inspection)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('--- KIỂU DỮ LIỆU BAN ĐẦU CỦA CÁC CỘT (DTYPES) ---')\n",
            "print(df.dtypes)\n",
            "\n",
            "print('\\n--- TỔNG QUAN BẢNG DỮ LIỆU THÔ ---')\n",
            "df.info()\n",
            "\n",
            "print('\\n--- ĐẾM CÁC DÒNG CÓ KÝ TỰ THIẾU \\\\N TRONG DỮ LIỆU IMDB ---')\n",
            "for col in df.columns:\n",
            "    count_n = (df[col].astype(str) == r'\\N').sum()\n",
            "    if count_n > 0:\n",
            "        print(f'Cột \"{col}\" có {count_n:,} dòng chứa ký tự \"\\\\N\" cần xử lý!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 3. Thực hiện Ép kiểu dữ liệu (Type Casting) & Xử lý Missing Values"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# 1. Ép kiểu năm phát hành (year) sang số nguyên int32\n",
            "df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('int32')\n",
            "\n",
            "# 2. Xử lý thời lượng phim (runtime_minutes):\n",
            "# - Thay '\\N' bằng NaN\n",
            "# - Chuyển sang số\n",
            "# - Điền giá trị trung vị (median) cho phim thiếu thời lượng\n",
            "df['runtime_minutes'] = df['runtime_minutes'].replace(r'\\N', np.nan)\n",
            "df['runtime_minutes'] = pd.to_numeric(df['runtime_minutes'], errors='coerce')\n",
            "median_runtime = df['runtime_minutes'].median()\n",
            "df['runtime_minutes'] = df['runtime_minutes'].fillna(median_runtime).astype('int32')\n",
            "\n",
            "# 3. Ép kiểu điểm số (rating) sang float64 và lượt vote sang int64\n",
            "df['rating'] = pd.to_numeric(df['rating'], errors='coerce').astype('float64')\n",
            "df['votes'] = pd.to_numeric(df['votes'], errors='coerce').astype('int64')\n",
            "\n",
            "# 4. Làm sạch thể loại (genres):\n",
            "# - Thay '\\N' bằng 'Unknown'\n",
            "# - Tạo chuỗi genres_clean (thay dấu phẩy bằng khoảng trắng)\n",
            "# - Tạo cột genres_list dạng mảng Python\n",
            "df['genres'] = df['genres'].replace(r'\\N', 'Unknown').fillna('Unknown')\n",
            "df['genres_clean'] = df['genres'].str.replace(',', ' ')\n",
            "df['genres_list'] = df['genres'].apply(lambda g: [x.strip() for x in g.split(',') if x.strip()])\n",
            "\n",
            "# 5. Bổ sung các đường dẫn hỗ trợ Web App\n",
            "df['imdb_url'] = 'https://www.imdb.com/title/' + df['id'] + '/'\n",
            "df['watch_url'] = 'https://2embed.cc/embed/' + df['id']\n",
            "\n",
            "print('✅ Đã hoàn tất toàn bộ các bước ép kiểu và làm sạch!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Kiểm tra lại dữ liệu sau khi ép kiểu & so sánh"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('--- KIỂU DỮ LIỆU CHUẨN SAU KHI ÉP KIỂU (DTYPES MỚI) ---')\n",
            "print(df.dtypes)\n",
            "\n",
            "print('\\n--- KIỂM TRA LẠI THÔNG TIN VÀ CÁC GIÁ TRỊ NULL ---')\n",
            "df.info()\n",
            "\n",
            "print('\\n--- 5 BẢN GHI ĐẦU TIÊN SAU KHI LÀM SẠCH ---')\n",
            "display(df.head(5))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Lưu dữ liệu đã làm sạch vào thư mục `data/interim/`"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "output_dir = 'data/interim'\n",
            "os.makedirs(output_dir, exist_ok=True)\n",
            "\n",
            "clean_csv_path = os.path.join(output_dir, 'cleaned_movies_2000_2026.csv')\n",
            "clean_json_path = os.path.join(output_dir, 'cleaned_movies_2000_2026.json')\n",
            "\n",
            "df.to_csv(clean_csv_path, index=False, encoding='utf-8-sig')\n",
            "df.to_json(clean_json_path, orient='records', force_ascii=False, indent=2)\n",
            "\n",
            "print(f'✅ Đã lưu file sạch CSV: {clean_csv_path}')\n",
            "print(f'✅ Đã lưu file sạch JSON: {clean_json_path}')\n",
            "print('\\n👉 BƯỚC TIẾP THEO: Hãy mở file `03_Exploratory_Data_Analysis.ipynb` để phân tích thống kê và vẽ biểu đồ!')"
        ]
    }
]

# ==============================================================================
# NOTEBOOK 3: KHÁM PHÁ & TRỰC QUAN HÓA DỮ LIỆU (EDA)
# ==============================================================================
nb3_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 📊 PHẦN 3: PHÂN TÍCH THỐNG KÊ & KHÁM PHÁ DỮ LIỆU (EDA)\n",
            "## File: `03_Exploratory_Data_Analysis.ipynb`\n",
            "---\n",
            "**Mục tiêu của phần này:**\n",
            "1. Đọc dữ liệu sạch từ `data/interim/cleaned_movies_2000_2026.csv`.\n",
            "2. Thống kê mô tả các biến số (Mean, Min, Max, Quantile của Year, Runtime, Rating, Votes).\n",
            "3. Phân tích phân bố số lượng phim qua các năm từ **2000 đến 2026** và vẽ biểu đồ cột.\n",
            "4. Phân tích phân bố điểm đánh giá (`rating`) bằng biểu đồ Histogram.\n",
            "5. Phân tích tần suất các thể loại phim (Top genres) bằng biểu đồ thanh ngang.\n",
            "6. Tìm ra Top 10 phim thịnh hành nhất và phân tích tương quan thời lượng - điểm số."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Khai báo thư viện & Nạp dữ liệu sạch"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "# Thiết lập kích thước đồ thị mặc định\n",
            "plt.rcParams['figure.figsize'] = (10, 5)\n",
            "plt.rcParams['font.size'] = 11\n",
            "\n",
            "df = pd.read_csv('data/interim/cleaned_movies_2000_2026.csv')\n",
            "print(f'✅ Đã nạp thành công {len(df):,} bộ phim!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Bảng Thống kê mô tả (Descriptive Statistics)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('--- THỐNG KÊ MÔ TẢ CÁC BIẾN SỐ CHÍNH ---')\n",
            "display(df[['year', 'runtime_minutes', 'rating', 'votes']].describe().round(2))\n",
            "\n",
            "print(f\"Thời lượng trung bình: {df['runtime_minutes'].mean():.1f} phút\")\n",
            "print(f\"Điểm đánh giá trung bình: {df['rating'].mean():.2f} / 10\")"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 3. Phân bố số lượng phim theo năm (2000 - 2026)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "year_counts = df['year'].value_counts().sort_index()\n",
            "\n",
            "# Vẽ biểu đồ cột\n",
            "plt.figure(figsize=(12, 5))\n",
            "plt.bar(year_counts.index, year_counts.values, color='#3b82f6', edgecolor='#1d4ed8')\n",
            "plt.title('Phân Bố Số Lượng Phim Theo Năm Phát Hành (2000 - 2026)', fontsize=14, fontweight='bold')\n",
            "plt.xlabel('Năm phát hành')\n",
            "plt.ylabel('Số lượng phim')\n",
            "plt.grid(axis='y', linestyle='--', alpha=0.5)\n",
            "plt.xticks(year_counts.index, rotation=45)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Phân bố điểm số IMDb Rating"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Vẽ biểu đồ histogram điểm số\n",
            "plt.figure(figsize=(10, 5))\n",
            "plt.hist(df['rating'], bins=30, color='#10b981', edgecolor='#047857')\n",
            "plt.axvline(df['rating'].mean(), color='red', linestyle='dashed', linewidth=2, label=f'Điểm TB: {df[\"rating\"].mean():.2f}')\n",
            "plt.title('Phân Bố Điểm Đánh Giá IMDb Rating', fontsize=14, fontweight='bold')\n",
            "plt.xlabel('Điểm số (Thang 1.0 - 10.0)')\n",
            "plt.ylabel('Tần suất (Số phim)')\n",
            "plt.legend()\n",
            "plt.grid(axis='y', linestyle='--', alpha=0.5)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Top 15 Thể loại phim phổ biến nhất"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Tách toàn bộ thể loại\n",
            "all_genres = []\n",
            "for item in df['genres'].dropna():\n",
            "    all_genres.extend([g.strip() for g in item.split(',') if g.strip() and g.strip() != 'Unknown'])\n",
            "\n",
            "genre_series = pd.Series(all_genres).value_counts().head(15)\n",
            "\n",
            "# Vẽ biểu đồ thanh ngang\n",
            "plt.figure(figsize=(10, 6))\n",
            "plt.barh(genre_series.index[::-1], genre_series.values[::-1], color='#8b5cf6', edgecolor='#6d28d9')\n",
            "plt.title('Top 15 Thể Loại Phim Xuất Hiện Nhiều Nhất (2000 - 2026)', fontsize=14, fontweight='bold')\n",
            "plt.xlabel('Số phim gắn tag thể loại')\n",
            "plt.grid(axis='x', linestyle='--', alpha=0.5)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 6. Top 10 Bộ phim thịnh hành nhất (Nhiều lượt đánh giá nhất)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "top10_popular = df.sort_values(by='votes', ascending=False)[['title', 'year', 'genres', 'rating', 'votes']].head(10)\n",
            "display(top10_popular)\n",
            "print('\\n👉 BƯỚC TIẾP THEO: Hãy mở file `04_Feature_Engineering_And_Recommendation.ipynb` để xây dựng mô hình gợi ý!')"
        ]
    }
]

# ==============================================================================
# NOTEBOOK 4: TRÍCH CHỌN ĐẶC TRƯNG & XÂY DỰNG MÔ HÌNH GỢI Ý
# ==============================================================================
nb4_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 🤖 PHẦN 4: TRÍCH CHỌN ĐẶC TRƯNG & MÔ HÌNH GỢI Ý (RECOMMENDATION ENGINE)\n",
            "## File: `04_Feature_Engineering_And_Recommendation.ipynb`\n",
            "---\n",
            "**Mục tiêu của phần này:**\n",
            "1. Đọc dữ liệu sạch từ `data/interim/cleaned_movies_2000_2026.csv`.\n",
            "2. **Feature Engineering**:\n",
            "   - Tính điểm xếp hạng có trọng số IMDb Bayesian Weighted Rating (WR).\n",
            "   - Tạo chuỗi đặc trưng tổng hợp (`combined_features`) từ Tên phim + Thể loại (nhân đôi trọng số).\n",
            "3. **Xây dựng mô hình Gợi Ý Lọc Dựa Trên Nội Dung (Content-Based Filtering)**:\n",
            "   - Xây dựng ma trận TF-IDF Vectorizer (`max_features=5000`).\n",
            "   - Tính độ tương đồng Cô-sin (Cosine Similarity Matrix).\n",
            "4. Thử nghiệm hàm gợi ý phim tương tự khi người dùng nhập tên phim.\n",
            "5. Xuất dữ liệu hoàn chỉnh ra `data/processed/movies_20000_2000_2026.csv` và `.json` để tích hợp vào Web App."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Khai báo thư viện & Nạp dữ liệu"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "from sklearn.feature_extraction.text import TfidfVectorizer\n",
            "from sklearn.metrics.pairwise import cosine_similarity\n",
            "\n",
            "df = pd.read_csv('data/interim/cleaned_movies_2000_2026.csv')\n",
            "print(f'✅ Đã nạp thành công {len(df):,} bộ phim!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Feature Engineering: Tính điểm Bayesian Weighted Rating (WR)\n",
            "Công thức chuẩn hóa của IMDb:\n",
            "$$WR = \\left( \\frac{v}{v + m} \\right) \\times R + \\left( \\frac{m}{v + m} \\right) \\times C$$\n",
            "- $v$: Số lượt vote của phim\n",
            "- $m$: Ngưỡng vote phân vị 70%\n",
            "- $R$: Điểm rating trung bình của phim\n",
            "- $C$: Điểm trung bình toàn bộ 20.000 phim"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "C = df['rating'].mean()\n",
            "m = df['votes'].quantile(0.70)\n",
            "\n",
            "def bayesian_weighted_rating(row):\n",
            "    v = row['votes']\n",
            "    R = row['rating']\n",
            "    return (v / (v + m)) * R + (m / (v + m)) * C\n",
            "\n",
            "df['weighted_rating'] = df.apply(bayesian_weighted_rating, axis=1).round(2)\n",
            "\n",
            "print(f'Điểm trung bình (C): {C:.2f}')\n",
            "print(f'Ngưỡng vote phân vị 70% (m): {m:,.0f} votes')\n",
            "display(df.sort_values(by='weighted_rating', ascending=False)[['title', 'year', 'rating', 'votes', 'weighted_rating']].head(5))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 3. Tạo chuỗi đặc trưng tổng hợp (`combined_features`)\n",
            "Ghép Tên phim và Thể loại để làm đầu vào cho thuật toán TF-IDF."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Ghép chuỗi đặc trưng: Tên phim + Thể loại (lặp 2 lần để tăng trọng số thể loại)\n",
            "df['combined_features'] = df['title'] + ' ' + df['genres_clean'] + ' ' + df['genres_clean']\n",
            "print('Ví dụ chuỗi đặc trưng của phim đầu tiên:')\n",
            "print(df['combined_features'].iloc[0])"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Xây dựng ma trận TF-IDF & Hàm Gợi Ý Cosine Similarity"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('⏳ Đang tính toán ma trận TF-IDF cho 20.000 phim...')\n",
            "tfidf = TfidfVectorizer(stop_words='english', max_features=5000)\n",
            "tfidf_matrix = tfidf.fit_transform(df['combined_features'])\n",
            "print(f'✅ Kích thước ma trận đặc trưng TF-IDF: {tfidf_matrix.shape}')\n",
            "\n",
            "# Tạo tra cứu vị trí index theo tên phim (không phân biệt chữ hoa/thường)\n",
            "indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()\n",
            "\n",
            "def recommend_movies(movie_title, top_n=5):\n",
            "    query = movie_title.lower().strip()\n",
            "    if query not in indices:\n",
            "        return f\"Không tìm thấy phim '{movie_title}' trong kho 20.000 phim.\"\n",
            "    \n",
            "    idx = indices[query]\n",
            "    # Tính độ tương đồng giữa phim được chọn và toàn bộ kho phim\n",
            "    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()\n",
            "    # Lấy top các phim có độ tương đồng cao nhất (bỏ qua chính nó)\n",
            "    top_idx = sim_scores.argsort()[::-1][1:top_n+1]\n",
            "    \n",
            "    result = df.iloc[top_idx][['title', 'year', 'genres', 'rating', 'weighted_rating']].copy()\n",
            "    result['similarity_score'] = sim_scores[top_idx].round(3)\n",
            "    return result\n",
            "\n",
            "print('Đã khởi tạo xong hàm gợi ý phim!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Thử nghiệm hàm gợi ý trên các bộ phim kinh điển"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print(\"🎯 GỢI Ý CÁC PHIM TƯƠNG TỰ VỚI 'Inception (2010)':\")\n",
            "display(recommend_movies('Inception', top_n=5))\n",
            "\n",
            "print(\"\\n🎯 GỢI Ý CÁC PHIM TƯƠNG TỰ VỚI 'The Dark Knight (2008)':\")\n",
            "display(recommend_movies('The Dark Knight', top_n=5))\n",
            "\n",
            "print(\"\\n🎯 GỢI Ý CÁC PHIM TƯƠNG TỰ VỚI 'Interstellar (2014)':\")\n",
            "display(recommend_movies('Interstellar', top_n=5))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 6. Xuất tập dữ liệu sạch hoàn chỉnh ra `data/processed/`\n",
            "Lưu dataset chuẩn cuối cùng để Backend FastAPI và Web App sử dụng trực tiếp."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "output_dir = 'data/processed'\n",
            "os.makedirs(output_dir, exist_ok=True)\n",
            "\n",
            "final_csv_path = os.path.join(output_dir, 'movies_20000_2000_2026.csv')\n",
            "final_json_path = os.path.join(output_dir, 'movies_20000_2000_2026.json')\n",
            "\n",
            "df.to_csv(final_csv_path, index=False, encoding='utf-8-sig')\n",
            "df.to_json(final_json_path, orient='records', force_ascii=False, indent=2)\n",
            "\n",
            "print(f'✅ Đã xuất dataset CSV hoàn chỉnh: {final_csv_path} ({os.path.getsize(final_csv_path)/1024/1024:.2f} MB)')\n",
            "print(f'✅ Đã xuất dataset JSON hoàn chỉnh: {final_json_path} ({os.path.getsize(final_json_path)/1024/1024:.2f} MB)')\n",
            "print('\\n🎉 CHÚC MỪNG BẠN! TOÀN BỘ PIPELINE TỪ CRAWL -> LÀM SẠCH -> EDA -> MODEL GỢI Ý ĐÃ HOÀN TẤT!')"
        ]
    }
]

# Ghi ra 4 file notebook
notebooks_list = [
    ("notebooks/01_Crawl_IMDb_Data.ipynb", nb1_cells),
    ("notebooks/02_Data_Cleaning_And_Type_Casting.ipynb", nb2_cells),
    ("notebooks/03_Exploratory_Data_Analysis.ipynb", nb3_cells),
    ("notebooks/04_Feature_Engineering_And_Recommendation.ipynb", nb4_cells)
]

for filename, cells in notebooks_list:
    nb_dict = make_nb(cells)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(nb_dict, f, ensure_ascii=False, indent=2)
    print(f"Created: {filename}")

print("\nHoan thanh viec chia nho 4 file Notebook!")
