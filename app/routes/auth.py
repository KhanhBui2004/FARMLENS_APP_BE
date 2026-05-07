from datetime import datetime

import bcrypt
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId

from app.models.users import RefreshRequest, UserCreate, UserLogin
from app.config.database import user_collection
from app.schema.user import user_serial
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_jwt_error
)

router = APIRouter(prefix="/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message
        }
    )


@router.post("/register")
async def register_user(user: UserCreate):
    existing_user = user_collection.find_one(
        {"$or": [{"username": user.username}, {"email": user.email}]}
    )
    if existing_user:
        return error_response(409, "Username or email already exists")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["created_at"] = datetime.utcnow()

    result = user_collection.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return {
        "code": 201,
        "message": "User registered successfully",
        "user": user_serial(user_dict)}


@router.post("/login")
async def login_user(login: UserLogin):
    user = user_collection.find_one(
        {"$or": [{"username": login.identifier}, {"email": login.identifier}]}
    )
    if not user:
        return error_response(401, "Invalid credentials")

    if not verify_password(login.password, user.get("password", "")):
        return error_response(401, "Invalid credentials")

    access_token = create_access_token(
        subject=str(user["_id"]),
        username=user.get("username", ""),
        email=user.get("email", "")
    )
    refresh_token = create_refresh_token(subject=str(user["_id"]))

    return {
        "code": 200,
        "message": "Login successful",
        "user": user_serial(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest):
    try:
        token_data = decode_token(payload.refresh_token)
    except Exception as error:
        if is_jwt_error(error):
            return error_response(401, "Invalid refresh token")
        return error_response(500, "Unexpected error")

    if token_data.get("token_type") != "refresh":
        return error_response(401, "Invalid refresh token")

    user_id = token_data.get("sub")
    if not user_id:
        return error_response(401, "Invalid refresh token")

    try:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return error_response(401, "Invalid refresh token")

    if not user:
        return error_response(401, "Invalid refresh token")

    access_token = create_access_token(
        subject=str(user["_id"]),
        username=user.get("username", ""),
        email=user.get("email", "")
    )
    new_refresh_token = create_refresh_token(subject=str(user["_id"]))

    return {
        "code": 200,
        "message": "Token refreshed successfully",
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
