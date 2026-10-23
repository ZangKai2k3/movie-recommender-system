# -*- coding: utf-8 -*-
import json
import os

os.makedirs('notebooks', exist_ok=True)

cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 🎬 ĐỒ ÁN HỆ THỐNG GỢI Ý PHIM (MOVIE RECOMMENDATION SYSTEM)\n",
            "## NOTEBOOK: THU THẬP, TIỀN XỬ LÝ & KHÁM PHÁ DỮ LIỆU IMDB (2000 - 2026)\n",
            "---\n",
            "**Mục tiêu của Notebook:**\n",
            "1. **Khai báo thư viện**: `urllib`, `gzip`, `pandas`, `numpy`, `sklearn`.\n",
            "2. **Crawl dữ liệu**: Thu thập trực tiếp **20.000 bộ phim** từ IMDb giai đoạn **2000 - 2026** qua HTTP Stream tốc độ cao.\n",
            "3. **Khám phá dữ liệu thô (EDA sơ bộ)**: Xem `head()`, `info()`, `shape`, cấu trúc bảng và các giá trị thiếu.\n",
            "4. **Tiền xử lý & Ép kiểu dữ liệu (Data Cleaning & Type Casting)**: Ép kiểu `int`, `float`, xử lý missing value (`\\N`), làm sạch thể loại.\n",
            "5. **Phân tích Thống kê (EDA)**: Phân bố số lượng phim theo năm (2000 - 2026), top thể loại, top phim điểm cao.\n",
            "6. **Trích chọn đặc trưng (Feature Engineering)**: Điểm Bayesian Weighted Rating (WR) & chuỗi đặc trưng gợi ý `combined_features`.\n",
            "7. **Thử nghiệm mô hình gợi ý Content-Based**: TF-IDF & Cosine Similarity ngay trong notebook.\n",
            "8. **Xuất dữ liệu sạch**: Lưu file `CSV` và `JSON` phục vụ Backend FastAPI & ReactJS."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Khai Báo Các Thư Viện Cần Thiết\n",
            "Thực hiện import các thư viện khoa học dữ liệu và xử lý luồng mạng chuẩn của Python."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import json\n",
            "import re\n",
            "import time\n",
            "import gzip\n",
            "import urllib.request\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "\n",
            "# Cấu hình Pandas hiển thị dữ liệu bảng đẹp và không bị cắt dòng\n",
            "pd.set_option('display.max_columns', None)\n",
            "pd.set_option('display.max_rows', 20)\n",
            "pd.set_option('display.width', 1000)\n",
            "\n",
            "print('✅ Đã nạp thành công các thư viện cơ bản!')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Thiết Lập Cấu Hình & Tiêu Chí Lọc Dữ Liệu\n",
            "Đặt các điều kiện lọc theo yêu cầu bài toán:\n",
            "- **Số lượng phim**: 20.000 phim\n",
            "- **Năm phát hành**: Từ 2000 đến 2026\n",
            "- **Loại phim**: Phim điện ảnh (`movie`, `tvMovie`)\n",
            "- **Nội dung người lớn**: Loại bỏ 100% phim 18+ (`isAdult == 0`)\n",
            "- **Ngưỡng bình chọn**: `>= 100 votes` để đảm bảo chất lượng và độ tin cậy"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Cấu hình tham số thu thập dữ liệu\n",
            "TARGET_LIMIT = 20000        # Số lượng phim mục tiêu\n",
            "START_YEAR = 2000           # Năm bắt đầu\n",
            "END_YEAR = 2026             # Năm kết thúc\n",
            "MIN_VOTES = 100             # Số lượt đánh giá tối thiểu\n",
            "\n",
            "ALLOWED_TITLE_TYPES = {'movie', 'tvMovie'}  # Chỉ lấy phim điện ảnh\n",
            "EXCLUDE_ADULT = True                         # Không lấy phim người lớn\n",
            "\n",
            "# URL luồng dữ liệu mở chính thức từ IMDb\n",
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
            "### 3. Thu Thập Dữ Liệu IMDb Theo Luồng (Streaming HTTP)\n",
            "**Kỹ thuật tối ưu**: Đọc trực tiếp luồng gzip qua mạng theo từng dòng mà không cần tải file lớn xuống ổ cứng, xử lý xong trong vài chục giây."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# 3.1. Quét luồng Ratings để lấy điểm đánh giá và lọc theo độ phổ biến\n",
            "print('⏳ [1/2] Đang quét luồng IMDb Ratings...')\n",
            "t0 = time.time()\n",
            "req_ratings = urllib.request.Request(RATINGS_URL, headers={'User-Agent': 'Mozilla/5.0'})\n",
            "ratings = {}\n",
            "\n",
            "with urllib.request.urlopen(req_ratings, timeout=30) as response:\n",
            "    with gzip.GzipFile(fileobj=response) as gz_stream:\n",
            "        gz_stream.readline()  # Bỏ qua dòng tiêu đề\n",
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
            "# Sắp xếp theo votes giảm dần và lấy tập ứng viên đệm (70.000 phim)\n",
            "sorted_ratings = sorted(ratings.items(), key=lambda x: x[1][1], reverse=True)\n",
            "candidate_ids = {item[0] for item in sorted_ratings[:70000]}\n",
            "\n",
            "# 3.2. Quét luồng Basics để lấy tên, năm, thời lượng, thể loại trong giai đoạn 2000 - 2026\n",
            "print(f'⏳ [2/2] Đang quét luồng IMDb Basics lọc phim giai đoạn {START_YEAR} - {END_YEAR}...')\n",
            "t1 = time.time()\n",
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
            "            if tconst in candidate_ids:\n",
            "                title_type = parts[1]\n",
            "                is_adult = parts[4]\n",
            "                year_str = parts[5]\n",
            "                \n",
            "                # Điều kiện lọc: Loại phim điện ảnh + Không nội dung người lớn + Có năm phát hành\n",
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
            "print(f'-> Đã trích xuất {len(raw_movie_list):,} phim phù hợp trong {time.time() - t1:.2f} giây.')\n",
            "\n",
            "# Sắp xếp lại theo độ thịnh hành (votes giảm dần) và lấy đúng 20.000 phim\n",
            "raw_movie_list.sort(key=lambda m: m['votes'], reverse=True)\n",
            "final_movies = raw_movie_list[:TARGET_LIMIT]\n",
            "\n",
            "# Đưa dữ liệu thô vào Pandas DataFrame\n",
            "df_raw = pd.DataFrame(final_movies)\n",
            "print(f'\\n🎉 Thu thập hoàn tất! Đã nạp thành công {len(df_raw):,} dòng dữ liệu vào DataFrame thô (df_raw).')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Khám Phá Dữ Liệu Thô (Initial Data Inspection / EDA sơ bộ)\n",
            "Quan sát hình dạng dữ liệu, kiểu dữ liệu ban đầu, và kiểm tra các giá trị thiếu hoặc ký tự `\\N` của IMDb."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('--- 10 BẢN GHI ĐẦU TIÊN ---')\n",
            "display(df_raw.head(10))\n",
            "\n",
            "print('\\n--- KÍCH THƯỚC DỮ LIỆU (SHAPE) ---')\n",
            "print(f'Số dòng: {df_raw.shape[0]:,} | Số cột: {df_raw.shape[1]}')\n",
            "\n",
            "print('\\n--- THÔNG TIN CẤU TRÚC VÀ KIỂU DỮ LIỆU BAN ĐẦU ---')\n",
            "df_raw.info()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "**Nhận xét dữ liệu thô:**\n",
            "- Cột `runtime_minutes` đang bị lưu ở dạng chuỗi (`object`) thay vì số nguyên, và có chứa ký tự `\\N` đối với các phim chưa công bố thời lượng.\n",
            "- Cột `genres` chứa ký tự `\\N` đối với phim không rõ thể loại.\n",
            "- Cần tiến hành bước **Tiền xử lý & Ép kiểu dữ liệu (Data Cleaning & Type Casting)** ngay dưới đây."
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Tiền Xử Lý & Ép Kiểu Dữ Liệu (Data Cleaning & Type Casting)\n",
            "Các bước xử lý chuẩn chỉnh:\n",
            "1. Tạo bản sao `df = df_raw.copy()` để không làm hỏng dữ liệu gốc.\n",
            "2. Ép kiểu `year`: Đảm bảo là kiểu số nguyên `int32`.\n",
            "3. Xử lý `runtime_minutes`: Thay thế `\\N` bằng `NaN`, sau đó chuyển thành kiểu số thực/số nguyên và điền giá trị trung vị (`median`) cho các phim thiếu thời lượng.\n",
            "4. Xử lý `genres`: Thay thế `\\N` bằng rỗng `\"Unknown\"`, chuẩn hóa chuỗi và tạo thêm cột `genres_list` dạng mảng `[Action, Drama]`.\n",
            "5. Ép kiểu `rating` sang `float64` và `votes` sang `int64`.\n",
            "6. Tạo đường dẫn `imdb_url` và `watch_url` để sẵn sàng phát phim."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Tạo bản sao làm việc\n",
            "df = df_raw.copy()\n",
            "\n",
            "# 1. Ép kiểu năm phát hành (year)\n",
            "df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('int32')\n",
            "\n",
            "# 2. Xử lý và ép kiểu thời lượng (runtime_minutes)\n",
            "# Thay thế chuỗi '\\N' thành NaN rồi chuyển sang số thực\n",
            "df['runtime_minutes'] = df['runtime_minutes'].replace(r'\\N', np.nan)\n",
            "df['runtime_minutes'] = pd.to_numeric(df['runtime_minutes'], errors='coerce')\n",
            "\n",
            "# Điền giá trị trung vị (median) của các phim cùng thời kỳ cho các phim bị thiếu thời lượng\n",
            "median_runtime = df['runtime_minutes'].median()\n",
            "df['runtime_minutes'] = df['runtime_minutes'].fillna(median_runtime).astype('int32')\n",
            "\n",
            "# 3. Ép kiểu điểm số (rating) và lượt bình chọn (votes)\n",
            "df['rating'] = pd.to_numeric(df['rating'], errors='coerce').astype('float64')\n",
            "df['votes'] = pd.to_numeric(df['votes'], errors='coerce').astype('int64')\n",
            "\n",
            "# 4. Xử lý thể loại (genres)\n",
            "df['genres'] = df['genres'].replace(r'\\N', 'Unknown').fillna('Unknown')\n",
            "df['genres_clean'] = df['genres'].str.replace(',', ' ')\n",
            "df['genres_list'] = df['genres'].apply(lambda g: [x.strip() for x in g.split(',') if x.strip()])\n",
            "\n",
            "# 5. Bổ sung các đường dẫn hỗ trợ hệ thống\n",
            "df['imdb_url'] = 'https://www.imdb.com/title/' + df['id'] + '/'\n",
            "df['watch_url'] = 'https://2embed.cc/embed/' + df['id']\n",
            "\n",
            "print('✅ Hoàn tất ép kiểu và làm sạch dữ liệu!')\n",
            "print('\\n--- KIỂM TRA LẠI DTYPES VÀ MISSING VALUES SAU KHI XỬ LÝ ---')\n",
            "df.info()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 6. Khám Phá Thống Kê & Phân Tích Dữ Liệu (EDA - Exploratory Data Analysis)\n",
            "Kiểm tra thống kê mô tả, phân bố phim qua các năm 2000 - 2026 và các thể loại phổ biến nhất."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('--- 1. BẢNG THỐNG KÊ MÔ TẢ (DESCRIPTIVE STATISTICS) ---')\n",
            "display(df[['year', 'runtime_minutes', 'rating', 'votes']].describe())\n",
            "\n",
            "print('\\n--- 2. PHÂN BỐ SỐ LƯỢNG PHIM THEO NĂM (2000 - 2026) ---')\n",
            "year_counts = df['year'].value_counts().sort_index()\n",
            "display(year_counts.to_frame(name='Số lượng phim'))\n",
            "\n",
            "print('\\n--- 3. TOP 10 THỂ LOẠI XUẤT HIỆN NHIỀU NHẤT ---')\n",
            "all_genres = [g for sublist in df['genres_list'] for g in sublist]\n",
            "genre_series = pd.Series(all_genres).value_counts()\n",
            "display(genre_series.head(10).to_frame(name='Số phim gắn tag thể loại'))\n",
            "\n",
            "print('\\n--- 4. TOP 10 BỘ PHIM ĐƯỢC BÌNH CHỌN NHIỀU NHẤT GIAI ĐOẠN 2000 - 2026 ---')\n",
            "top_popular = df.sort_values(by='votes', ascending=False)[['title', 'year', 'genres', 'rating', 'votes']].head(10)\n",
            "display(top_popular)"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 7. Trích Chọn Đặc Trưng (Feature Engineering)\n",
            "1. **Điểm xếp hạng có trọng số Bayesian Weighted Rating (WR) của IMDb**:\n",
            "   $$WR = \\left( \\frac{v}{v + m} \\right) \\times R + \\left( \\frac{m}{v + m} \\right) \\times C$$\n",
            "   Trong đó:\n",
            "   - $v$: Số lượt votes của bộ phim.\n",
            "   - $m$: Ngưỡng số votes tối thiểu (lấy phân vị thứ 70 để xếp vào top tin cậy).\n",
            "   - $R$: Điểm đánh giá trung bình của phim (rating).\n",
            "   - $C$: Điểm trung bình của toàn bộ 20.000 phim trong tập dữ liệu.\n",
            "\n",
            "2. **Chuỗi đặc trưng tổng hợp (`combined_features`)**:\n",
            "   Kết hợp Tên phim + 2 lần Thể loại (tăng trọng số gu thể loại) để làm đầu vào ma trận TF-IDF / Cosine Similarity."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# 1. Tính toán điểm Bayesian Weighted Rating\n",
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
            "# 2. Tạo chuỗi đặc trưng tổng hợp (Metadata Soup)\n",
            "df['combined_features'] = df['title'] + ' ' + df['genres_clean'] + ' ' + df['genres_clean']\n",
            "\n",
            "print(f'Điểm trung bình toàn bộ phim (C): {C:.2f}')\n",
            "print(f'Ngưỡng vote phân vị 70% (m): {m:,.0f} votes')\n",
            "print('\\n--- 5 BỘ PHIM CÓ ĐIỂM XẾP HẠNG TRỌNG SỐ (WEIGHTED RATING) CAO NHẤT ---')\n",
            "display(df.sort_values(by='weighted_rating', ascending=False)[['title', 'year', 'rating', 'votes', 'weighted_rating']].head(5))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 8. Thử Nghiệm Thuật Toán Gợi Ý (Content-Based Filtering)\n",
            "Xây dựng mô hình TF-IDF Vectorizer và Cosine Similarity để gợi ý các phim tương tự trực tiếp trong notebook."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Thử nghiệm tính toán gợi ý bằng TF-IDF và Cosine Similarity\n",
            "try:\n",
            "    from sklearn.feature_extraction.text import TfidfVectorizer\n",
            "    from sklearn.metrics.pairwise import cosine_similarity\n",
            "    \n",
            "    print('⏳ Đang xây dựng ma trận TF-IDF cho 20.000 phim...')\n",
            "    tfidf = TfidfVectorizer(stop_words='english', max_features=5000)\n",
            "    tfidf_matrix = tfidf.fit_transform(df['combined_features'])\n",
            "    print(f'Kích thước ma trận TF-IDF: {tfidf_matrix.shape}')\n",
            "    \n",
            "    # Tạo từ điển tra cứu vị trí index theo tên phim\n",
            "    indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()\n",
            "    \n",
            "    def recommend_similar_movies(movie_title, top_n=5):\n",
            "        query = movie_title.lower().strip()\n",
            "        if query not in indices:\n",
            "            return f\"Không tìm thấy phim '{movie_title}' trong kho 20.000 phim.\"\n",
            "        \n",
            "        idx = indices[query]\n",
            "        # Tính Cosine Similarity giữa phim này và toàn bộ 20.000 phim\n",
            "        cosine_sim = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()\n",
            "        # Lấy top các phim có độ tương đồng cao nhất (bỏ qua chính nó)\n",
            "        top_indices = cosine_sim.argsort()[::-1][1:top_n+1]\n",
            "        \n",
            "        results = df.iloc[top_indices][['title', 'year', 'genres', 'rating', 'weighted_rating']].copy()\n",
            "        results['similarity_score'] = cosine_sim[top_indices].round(3)\n",
            "        return results\n",
            "        \n",
            "    print(\"\\n🎯 THỬ NGHIỆM GỢI Ý PHIM TƯƠNG TỰ VỚI 'Inception (2010)':\")\n",
            "    display(recommend_similar_movies('Inception', top_n=5))\n",
            "    \n",
            "    print(\"\\n🎯 THỬ NGHIỆM GỢI Ý PHIM TƯƠNG TỰ VỚI 'The Dark Knight (2008)':\")\n",
            "    display(recommend_similar_movies('The Dark Knight', top_n=5))\n",
            "    \n",
            "except ImportError:\n",
            "    print('Chưa cài sklearn, bạn có thể chạy: pip install scikit-learn để kích hoạt cell này.')"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 9. Xuất Dữ Liệu Sạch (Export Cleaned Dataset)\n",
            "Lưu dataset 20.000 phim hoàn chỉnh ra cả 2 định dạng:\n",
            "1. **CSV** (`movies_20000_2000_2026.csv`): Dùng cho Pandas, Excel, huấn luyện mô hình.\n",
            "2. **JSON** (`movies_20000_2000_2026.json`): Dùng cho Backend FastAPI và Web App."
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
            "csv_path = os.path.join(output_dir, 'movies_20000_2000_2026.csv')\n",
            "json_path = os.path.join(output_dir, 'movies_20000_2000_2026.json')\n",
            "\n",
            "# Xuất CSV mã hóa utf-8-sig để mở trên Excel không bị lỗi font tiếng Việt\n",
            "df.to_csv(csv_path, index=False, encoding='utf-8-sig')\n",
            "print(f'✅ Đã xuất file CSV thành công: {csv_path} ({os.path.getsize(csv_path)/1024/1024:.2f} MB)')\n",
            "\n",
            "# Xuất JSON\n",
            "df.to_json(json_path, orient='records', force_ascii=False, indent=2)\n",
            "print(f'✅ Đã xuất file JSON thành công: {json_path} ({os.path.getsize(json_path)/1024/1024:.2f} MB)')\n",
            "\n",
            "print('\\n🎉 CHÚC MỪNG BẠN ĐÃ HOÀN THÀNH QUY TRÌNH THU THẬP & TIỀN XỬ LÝ 20.000 PHIM!')"
        ]
    }
]

notebook = {
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

# Ghi ra 2 file
root_nb = "HTGoiYPhim_Crawl_2000_2026.ipynb"
nb_dir_nb = os.path.join("notebooks", "crawl_and_preprocess_2000_2026.ipynb")

with open(root_nb, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

with open(nb_dir_nb, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print(f"Da tao xong notebook tai {root_nb} va {nb_dir_nb}")

