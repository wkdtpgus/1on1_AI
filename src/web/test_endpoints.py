from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.utils.mock_db import MOCK_USER_DATA

router = APIRouter()

@router.get("/api/users", summary="[테스트용] 목업 DB의 모든 사용자 목록 반환")
async def get_users():
    """사용자 목록 반환 API (user_id와 name)"""
    users = [{"user_id": user["user_id"], "name": user["name"]} for user in MOCK_USER_DATA]
    return JSONResponse(content=users)
