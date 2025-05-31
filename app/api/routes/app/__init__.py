"""
Module chứa các API routes cho ứng dụng.
"""

from .recommendation import router as recommendation_router

__all__ = [
    'recommendation_router',
] 