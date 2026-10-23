"""
Module cấu hình bộ ghi log (Logger) chuẩn cho toàn bộ hệ thống.
Hỗ trợ ghi đồng thời ra màn hình console và file log định dạng UTF-8.
"""

import os
import sys
import logging
from datetime import datetime

# Đảm bảo console trên Windows luôn hiển thị được Unicode / Tiếng Việt không bị lỗi CP1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def setup_logger(name: str = "HTGoiYPhim", log_file: str = None) -> logging.Logger:
    """
    Khởi tạo và cấu hình Logger chuẩn.
    
    Tham số:
        name (str): Tên định danh của logger (mặc định: 'HTGoiYPhim')
        log_file (str, optional): Đường dẫn tới file log. Nếu không truyền sẽ tạo tự động trong thư mục ./logs
        
    Trả về:
        logging.Logger: Đối tượng logger đã sẵn sàng sử dụng
    """
    logger = logging.getLogger(name)
    
    # Tránh gắn lặp handlers nếu đã được thiết lập trước đó
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Định dạng hiển thị log
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. Console Handler (hiển thị terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # 2. File Handler (ghi file nhật ký)
    if not log_file:
        os.makedirs("./logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"./logs/{name}_{timestamp}.log"
    else:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Không thể tạo file log tại {log_file}: {e}")
        
    return logger

