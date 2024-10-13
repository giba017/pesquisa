from datetime import datetime

import click
import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.core.settings import Settings
from app.models.models import User


@click.command()
@click.option(
    '--username', prompt=True, help='O nome de usuário para o superusuário.'
)
@click.option(
    '--password',
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help='A senha para o superusuário.',
)
@click.option('--email', prompt=True, help='O email do superusuário.')
@click.option(
    '--full-name', prompt=True, help='Nome completo do superusuário.'
)
def create_superuser(username: str, password: str, email: str, full_name: str):
    """Cria um novo superusuário no banco de dados."""

    hashed_password = get_password_hash(password)

    # Criação da sessão de banco de dados
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    session = create_local_session(engine)

    print(type(session))

    TIME_ZONE = 'America/Sao_Paulo'
    tz = pytz.timezone(TIME_ZONE)

    try:
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            full_name=full_name,
            is_superuser=True,
            is_staff=True,
            otp_auth_url='',
            otp_base32=User.create_otp_base32(),
            otp_created_at=datetime.now(tz),
        )

        session.add(user)
        session.commit()
        click.echo(f'Superusuário {username} criado com sucesso!')
    except Exception as e:
        session.rollback()
        click.echo(f'Erro ao criar o superusuário: {e}')
    finally:
        session.close()


def create_local_session(engine):
    """Cria uma sessão de banco de dados."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


if __name__ == '__main__':
    create_superuser()
