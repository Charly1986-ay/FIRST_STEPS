from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.db import get_db
from app.models.user import UserORM

from app.api.v1.auth.repository import UserRepository

password_hash = PasswordHash.recommended()

# Ruta por la cual el cliente se va autenticar -> de aca se obtiene el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')


credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"}
)

def raise_expired_token():
    return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token espirado',
            headers={'WWW-Authenticate': 'Bearer'}
    )

def invalid_credentials():
    return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credenciales inválidas'
    )

def raise_forbidden():
    return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='No tienes permisos suficientes'
    )

def decode_token(token: str) -> dict:
    payload = jwt.decode(jwt=token, key=Settings.JWT_SECRET, algorithms=[Settings.JWT_ALG])
    return payload

""" def create_access_token(data: dict, expire_delta: Optional[timedelta] = None):
    to_decode = data.copy()

    # el expire se calcula sumando los minutos al tiempo actual
    # si el expire_delta es None, se carga ACCESS_TOKEN_EXPIRE_MINUTES por defecto 
    expire = datetime.now(
        tz=timezone.utc) + (expire_delta or timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_decode.update({'exp': expire})
    token = jwt.encode(payload=to_decode, key=Settings.JWT_SECRET, algorithm=Settings.ALG)
    return token """

def create_access_token(sub: str, minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes or Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {'sub': sub, 'exp': expire}, 
        Settings.JWT_SECRET, 
        algorithm=Settings.JWT_ALG
    )

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> UserORM:    
    try:
        payload = decode_token(token)
        sub: Optional[str] = payload.get('sub')
        username: Optional[str] = payload.get('username')

        if not sub: raise credentials_exc
        #return {'email': sub, 'username': username}
        user_id = int(sub)
    
    except ExpiredSignatureError:
        raise raise_expired_token()
    except InvalidTokenError:
        raise credentials_exc
    except PyJWTError:
        raise invalid_credentials()
    
    user = db.get(UserORM, user_id)

    if not user or not user.is_active: raise invalid_credentials()
    return user

def hash_password(plain: str) -> str:
    return password_hash.hash(password=plain)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

def require_role(min_role: Literal['user', 'editor', 'admin']):
    order = {'user': 0, 'editor': 1, 'admin': 2}

    def evaluation(user: UserORM = Depends(get_current_user)) -> UserORM:
        if order[user.role] < order[min_role]:
            raise raise_forbidden()
        return user
    
    return evaluation


async def auth2_token(
    form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    repository = UserRepository(db=db)
    user = repository.get_by_email(form.username)
    if not user or not verify_password(
        form.password, user.hash_password): raise invalid_credentials()
    token = create_access_token(sub=str(user.id))
    return {'access_token': token, 'token_type': 'bearer'}

require_user = require_role('user')
require_editor = require_role('editor')
require_admin = require_role('admin')