from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from src.auth.constants import PASSWORD_MIN_LENGTH, USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AuthResponse(BaseModel):
    msg: str


class UserBase(BaseModel):
    username: str = Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    email: EmailStr


class UserCreate(UserBase):
    password: SecretStr = Field(min_length=PASSWORD_MIN_LENGTH)


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
