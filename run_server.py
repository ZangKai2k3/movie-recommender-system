#!/usr/bin/env python3
"""
File khởi chạy FastAPI Web Server bằng Uvicorn.
Chạy lệnh: python run_server.py
"""

import sys

# Thiết lập encoding UTF-8 cho Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" [KHỞI CHẠY BACKEND FASTAPI - HTGOIYPHIM]")
    print(" - Web API Server : http://127.0.0.1:8000")
    print(" - Swagger Docs   : http://127.0.0.1:8000/docs")
    print(" - ReDoc Docs     : http://127.0.0.1:8000/redoc")
    print("=" * 60 + "\n")
    
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

