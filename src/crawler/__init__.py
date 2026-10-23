"""
Package Crawler tự xây dựng cho Hệ Thống Gợi Ý Phim (HTGoiYPhim).
"""

from .config import CrawlerConfig
from .imdb_stream import IMDbDataStreamer
from .enricher import MovieEnricher
from .preprocessor import MovieDataPreprocessor
from .pipeline import MovieCrawlerPipeline

__all__ = [
    "CrawlerConfig",
    "IMDbDataStreamer",
    "MovieEnricher",
    "MovieDataPreprocessor",
    "MovieCrawlerPipeline"
]

