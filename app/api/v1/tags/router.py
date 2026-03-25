from ast import pattern
from http.client import HTTPException

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1.tags import repository
from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
from app.core.db import get_db
from app.core.security import require_admin, require_editor, require_user
from app.models.user import UserORM


router = APIRouter(prefix='/tags', tags=['tags'])

@router.post(
    '', 
    response_model=TagPublic, 
    response_description='Tag creado (OK)!', 
    status_code=status.HTTP_201_CREATED
)
def create_tag(
    tag: TagCreate, 
    db: Session = Depends(get_db), 
    _editor: UserORM = Depends(require_editor)
):
    repository = TagRepository(db=db)

    try:
        tag_created = repository.create_tag(name=tag.name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error al crear el Tag'
        )


@router.get('', response_model=dict)
def list_tags(        
    page: int = Query(
        1, ge=1
    ),
    per_page: int = Query(
        10, ge=1, le=100
    ),    
    order_by: str = Query(
        'id', pattern='^(id|name)$'
    ),
    direction: str = Query(
        'asc', pattern='^(asc|desc)$'
    ),
    search: str | None= Query(None),    
    db: Session = Depends(get_db)
):  
    repository = TagRepository(db=db)
    return repository.list_tags(
        search=search, 
        order_by=order_by, 
        direction=direction, 
        page=page, 
        per_page=per_page
    )

@router.put('/{tags_id}', response_model=TagPublic)
def upadate_tag(
    tag_id: int,
    playload: TagUpdate,
    db: Session = Depends(get_db), 
    _editor: UserORM = Depends(require_editor)
):
    repository = TagRepository(db=db)

    tag=repository.update(
        tag_id=tag_id, 
         name=playload.name
    )

    if not tag:
        raise HTTPException(
            status_code=404, 
            detail='Tag no encontrado'
        )

    try:        
        db.commit()
        db.refresh(tag)
        return TagPublic.model_validate(tag)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail='Error al actualizar el tag'
        )

@router.delete('/{tags_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,    
    db: Session = Depends(get_db), 
    _admin: UserORM = Depends(require_admin)
):
    repository = TagRepository(db=db)

    try:        
        if not repository.delete(tag_id=tag_id):
            raise HTTPException(
                status_code=500, 
                detail='Error al eliminar el tag'
            )
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail='Error al eliminar el tag'
        )  

@router.get('/popular/top')
def get_most_popular_tag(
    db: Session = Depends(get_db), 
    _user: UserORM = Depends(require_user)
):
    repository = TagRepository(db=db)
    row = repository.most_popular()

    if not row:
        raise HTTPException(
            status_code=404, 
            detail='No hay tag en uso'
        )
    return row