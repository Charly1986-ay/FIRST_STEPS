from fastapi.params import Path
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.auth.repository import UserRepository
from app.core.db import get_db
from app.models.user import UserORM
from .schemas import RoleUpdate, TokenResponse, UserCreate, UserLogin, UserPublic
from app.core.security import create_access_token, get_current_user, hash_password, verify_password, auth2_token, require_admin


router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(playload: UserCreate, db: Session = Depends(get_db)):
    repository = UserRepository(db=db)
    if repository.get_by_email(playload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email ya registrado'
        )
    user = repository.create(
        email=playload.email, 
        hashed_password=hash_password(playload.password),
        full_name=playload.full_name
    )
    db.commit()
    db.refresh(user)

    return UserPublic.model_validate(user)


@router.put("/role/{user_id}", response_model=UserPublic)
def set_role(
    user_id: int = Path(..., ge=1),
    payload: RoleUpdate = None,
    db: Session = Depends(get_db),
    _admin: UserORM = Depends(require_admin)
):
    repository = UserRepository(db)
    user = repository.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    updated = repository.set_role(user, payload.role)

    db.commit()
    db.refresh(updated)

    return UserPublic.model_validate(updated)


@router.post('/token')
async def token_endpoint(response=Depends(auth2_token)):
    return response


@router.post('/login', response_model = TokenResponse)
async def login(playload: UserLogin, db: Session = Depends(get_db)):
    repository = UserRepository(db=db)
    user = repository.get_by_email(playload.email)
    if not user or not verify_password(playload.password, user.hash_password): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credenciales inválidas'
        )
    token = create_access_token(sub=str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get('/me', response_model=UserPublic)
async def read_me(current: UserORM = Depends(get_current_user)):
    return UserPublic.model_validate(current)