from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class UserRegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class UserLoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=300,
    )

    new_password: str = Field(
        min_length=12,
        max_length=128,
    )


class ResetPasswordResponse(BaseModel):
    message: str
