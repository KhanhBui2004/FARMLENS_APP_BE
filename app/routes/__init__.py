from fastapi import APIRouter, Depends

from app.routes.auth import router as auth_router
from app.routes.analysis import router as analysis_router
from app.routes.visualization import router as visualization_router
from app.routes.change_detection import router as change_detection_router
from app.utils.jwt import get_current_user


router = APIRouter()
router.include_router(auth_router)
router.include_router(analysis_router, dependencies=[Depends(get_current_user)])
router.include_router(visualization_router, dependencies=[Depends(get_current_user)])
router.include_router(change_detection_router, dependencies=[Depends(get_current_user)])
