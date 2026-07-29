from fastapi import APIRouter

from app.routes.core_routes.query_route import router as query_router

router = APIRouter()
router.include_router(query_router)
