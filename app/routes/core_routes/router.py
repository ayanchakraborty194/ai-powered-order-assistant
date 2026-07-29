from fastapi import APIRouter

from app.routes.core_routes.query_route import router as query_router
from app.routes.core_routes.thread_route import router as thread_router

router = APIRouter()
router.include_router(query_router)
router.include_router(thread_router)