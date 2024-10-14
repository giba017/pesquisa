from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from pesquisa.models import TodoState

# from pesquisa.permissioes_schema import RolePublic


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
#    role: RolePublic


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


###############################################
#  ########### pesquisa ######################

class OpcaoSchema(BaseModel):
    texto: str = Field(..., title="Texto da Opção",
                       description="Texto da opção de resposta")


class PerguntaSchema(BaseModel):
    texto: str = Field(..., title="Texto da Pergunta",
                       description="Texto da pergunta")
    tipo: str = Field(
        ..., title="Tipo da Pergunta",
        description="Tipo da pergunta ('texto', 'select_single', 'select_multiple')",  # noqa: E501
        pattern="^(texto|select_single|select_multiple)$"
    )
    opcoes: List[OpcaoSchema] = Field(default_factory=list,
                                title="Opções",
                                description="Lista de opções\
                                     para perguntas de múltipla escolha")
    limite_respostas: Optional[int] = Field(
        None, title="Limite de Respostas",
        description="Limite opcional de respostas para a pergunta"
    )


class QuestionarioSchema(BaseModel):
    titulo: str = Field(...,
                        title="Título do Questionário",
                        description="Título do questionário")
    descricao: Optional[str] = Field(None, title="Descrição",
                                     description="Descrição do questionário")
    perguntas: List[PerguntaSchema] = Field(
        ..., title="Perguntas",
        description="Lista de perguntas no questionário"
    )
