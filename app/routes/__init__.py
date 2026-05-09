from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.analysis import router as analysis_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(analysis_router)
