from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from pesquisa.database import get_session
from pesquisa.models import User
from pesquisa.schemas import TokenData
from pesquisa.settings import Settings

pwd_context = PasswordHash.recommended()
oauth2_schema = OAuth2PasswordBearer(tokenUrl='auth/token')
settings = Settings()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})
    encoded_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


async def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_schema),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get('sub')
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except DecodeError:
        raise credentials_exception
    except ExpiredSignatureError:
        raise credentials_exception

    user = session.scalar(
        select(User).where(User.username == token_data.username)
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail='Inactive user')

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


def verify_token(token: str):
    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get('sub')
        if username is None:
            return False
        return True
    except ExpiredSignatureError:
        # raise HTTPException(
        # status_code=403, detail="Token is invalid or expired")
        return False


def verify_user_with_roles_and_permissions(
    current_user: User, roles: list[str] = [], permissions: list[str] = []
):
    # Se o usuário for um superusuário, ele tem todas as permissões
    if current_user.is_superuser:
        return current_user

    if 'is_superuser' in permissions:
        return current_user

    # Verifica se o usuário tem pelo menos um dos papéis (roles) exigidos
    if roles and not any(role.role.name in roles for role in current_user.roles):
        raise HTTPException(
            status_code=403,
            detail="Not enough role permissions",
        )

    # Verifica se o usuário tem todas as permissões exigidas
    if permissions:
        user_permissions = {
            perm.name
            for role in current_user.roles
            for perm in role.role.permissions
        }
        if not all(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
            )

    raise HTTPException(
        status_code=403,
        detail="Not enough permissions",
    )
