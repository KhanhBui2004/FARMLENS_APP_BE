from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.sentinelImage import router as sentinel_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(sentinel_router)
