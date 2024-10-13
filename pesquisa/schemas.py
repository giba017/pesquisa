from datetime import datetime

from app.models.models import TodoState
from app.schemas.permissioes_schema import RolePublic
from pydantic import BaseModel, ConfigDict, EmailStr


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str
    full_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    model_config = ConfigDict(from_attributes=True)


class UserFull(UserPublic):
    created_at: datetime
    updated_at: datetime


class UserQrCode(UserFull):
    qr_code: str


class ListUserFull(BaseModel):
    rows: list[UserFull]
    total_records: int


class UserPasswordUpdate(BaseModel):
    password: str


class UpdatePasswordRequest(BaseModel):
    password: str
    new_password: str


class UserList(BaseModel):
    users: list[UserPublic]
    total_records: int
    page: int
    page_size: int


class UserRolesIn(BaseModel):
    user_id: int
    role_id: int


class UserRolesOut(UserRolesIn):
    id: int
    role: RolePublic


class UserRolesList(BaseModel):
    rows: list[UserRolesOut]
    total_records: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class TodoSchema(BaseModel):
    title: str
    description: str
    state: TodoState


class TodoPublic(BaseModel):
    id: int
    title: str
    description: str
    state: TodoState


class TodoList(BaseModel):
    todos: list[TodoPublic]


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    state: TodoState | None = None
