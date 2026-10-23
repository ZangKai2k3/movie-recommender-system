#!/usr/bin/env python3
"""
Điểm chạy thử nghiệm Hệ Thống Gợi Ý Phim (Movie Recommendation CLI).
Cho phép tìm kiếm và nhận danh sách các phim tương đồng trực tiếp từ terminal.
"""

import sys

# Đảm bảo hiển thị Unicode tiếng Việt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import argparse
from src.recommender.content_based import ContentBasedRecommender

def main():
    parser = argparse.ArgumentParser(
        description="Chương trình gợi ý phim tương đồng dựa trên Nội dung (Content-Based Filtering)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--movie",
        type=str,
        default=None,
        help="Tên bộ phim bạn muốn tìm gợi ý (ví dụ: 'Inception', 'The Dark Knight', 'Interstellar')"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Số lượng phim gợi ý muốn nhận"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/processed/movies_10000.csv",
        help="Đường dẫn đến file dữ liệu phim đã cào"
    )
    
    args = parser.parse_args()
    
    # Kiểm tra file dữ liệu
    dataset_path = args.data
    if not os.path.exists(dataset_path):
        # Thử tìm các file csv khác trong data/processed/
        processed_dir = "data/processed"
        found_files = [os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith(".csv")] if os.path.exists(processed_dir) else []
        if found_files:
            dataset_path = found_files[0]
            print(f"[!] Không tìm thấy '{args.data}', tự động chuyển sang dùng file: {dataset_path}")
        else:
            print(f"[X] Lỗi: Không tìm thấy file dữ liệu tại '{args.data}'. Vui lòng chạy crawler trước!")
            sys.exit(1)
            
    print(f"\n[*] Đang nạp tập dữ liệu và khởi tạo mô hình gợi ý từ: {dataset_path}...")
    recommender = ContentBasedRecommender(dataset_path)
    print(f"[✓] Đã nạp thành công {len(recommender.df):,} bộ phim vào mô hình!\n")
    
    # Nhận tên phim từ đối số dòng lệnh hoặc nhập từ bàn phím
    movie_name = args.movie
    if not movie_name:
        try:
            movie_name = input("Nhập tên bộ phim bạn yêu thích (ví dụ: Inception, Avatar, Titanic): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát.")
            sys.exit(0)
            
    if not movie_name:
        movie_name = "Inception"
        print(f"[i] Không nhập tên, mặc định chọn: '{movie_name}'")
        
    try:
        results = recommender.recommend(movie_name, top_n=args.top)
        
        print(f"\n==================================================================")
        print(f" DANH SACH {len(results)} PHIM TUONG DONG VOI: '{movie_name.upper()}'")
        print(f"==================================================================")
        for i, m in enumerate(results, 1):
            print(f"\n{i}. {m['title']} ({m.get('year', 'N/A')})")
            print(f"   - Do tuong dong : {m['similarity_score'] * 100:.1f}%")
            print(f"   - The loai      : {m.get('genres', 'N/A')}")
            print(f"   - Diem danh gia : {m.get('rating', 'N/A')}/10 ({m.get('votes', 0):,} votes)")
            if m.get('recommendation_reason'):
                print(f"   - Ly do goi y   : {m['recommendation_reason']}")
            if m.get('cast'):
                print(f"   - Dien vien     : {m['cast']}")
            if m.get('imdb_url'):
                print(f"   - IMDb Link     : {m['imdb_url']}")
        print(f"\n==================================================================\n")
        
    except ValueError as e:
        print(f"\n[X] {e}")
        print("[*] Gợi ý: Hãy thử nhập một số tên phim phổ biến như: Inception, The Dark Knight, Interstellar, Avatar, Titanic, Pulp Fiction...")

if __name__ == "__main__":
    main()

