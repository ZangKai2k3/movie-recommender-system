"""Package chứa các API Routers của FastAPI."""
from .auth_router import router as auth_router
from .history_router import router as history_router
from .rating_router import router as rating_router
from .movie_router import router as movie_router

__all__ = ["auth_router", "history_router", "rating_router", "movie_router"]

