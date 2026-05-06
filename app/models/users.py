from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    phone: str


class UserLogin(BaseModel):
    identifier: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str
