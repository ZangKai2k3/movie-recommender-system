#!/usr/bin/env python3
"""
Điểm chạy chính (Entrypoint) cho Bộ Thu Thập Dữ Liệu Phim - Hệ Thống Gợi Ý Phim (HTGoiYPhim).
Chạy lệnh trực tiếp từ terminal / command prompt.
"""

import sys

# Thiết lập bảng mã UTF-8 cho Windows console tránh lỗi charmap cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
from src.utils.logger import setup_logger
from src.crawler.config import CrawlerConfig
from src.crawler.pipeline import MovieCrawlerPipeline

def main():
    parser = argparse.ArgumentParser(
        description="Bộ cào dữ liệu phim IMDb hiệu năng cao phục vụ Hệ thống Gợi ý Phim",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Số lượng phim mục tiêu cần thu thập (ví dụ: 1000, 5000, 10000)"
    )
    parser.add_argument(
        "--min-votes",
        type=int,
        default=1000,
        help="Ngưỡng số lượt bình chọn tối thiểu để lọc phim có độ phổ biến và tin cậy cao"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=12,
        help="Số luồng đồng thời khi tải Poster và Tóm tắt nội dung"
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Bỏ qua bước tải Poster và Tóm tắt (chế độ siêu tốc, chạy xong trong ~15 giây)"
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Tên file xuất ra (mặc định sẽ tự đặt là movies_{limit})"
    )
    
    args = parser.parse_args()
    
    # Thiết lập logger
    logger = setup_logger("MovieCrawler")
    config = CrawlerConfig()
    
    pipeline = MovieCrawlerPipeline(config=config, logger=logger)
    
    try:
        pipeline.execute(
            limit=args.limit,
            min_votes=args.min_votes,
            enrich_data=not args.no_enrich,
            workers=args.workers,
            output_name=args.output_name
        )
    except KeyboardInterrupt:
        logger.warning("\nQuá trình thu thập đã bị tạm dừng bởi người dùng. Tiến trình đã được lưu vào checkpoint.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi trong quá trình thực thi: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

