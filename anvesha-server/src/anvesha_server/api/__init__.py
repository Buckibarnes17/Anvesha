from fastapi import APIRouter

from .projects import router as projects_router
from .spans import router as spans_router
from .traces import router as traces_router

api_router = APIRouter()
api_router.include_router(projects_router)
api_router.include_router(traces_router)
api_router.include_router(spans_router)

__all__ = ["api_router"]
