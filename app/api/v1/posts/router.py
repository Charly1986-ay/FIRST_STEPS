import asyncio
import math
from sqlite3 import IntegrityError
from typing import Annotated, List, Literal, Optional, Union

from fastapi import APIRouter, File, HTTPException, Path, Query, Depends, UploadFile, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import get_db
from app.models.user import UserORM
from .schemas import (PostPublic, PaginatedPost, 
                      PostCreate, PostUpdate, 
                      PostSummary)
from .repository import PostRepository
from app.core.security import get_current_user, oauth2_scheme, require_admin, require_editor
from app.services.file_storages import save_uploaded_image

import time

router = APIRouter(prefix='/posts', tags=['posts'])


""" @router.get('/sync')
def sync_endpoint():
    time.sleep(8)
    return {'message': 'Función síncronica ha finalizado'}


@router.get('/async')
async def async_endpoint():
    await asyncio.sleep(8)
    return {'message': 'Función asíncronica ha finalizado'} """


@router.get("", response_model=PaginatedPost)
def list_posts(
    text: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Parámetro obsoleto, usa 'query o search' en su lugar."
    ),
    query: Optional[str] = Query(
        default=None,
        description="Texto para buscar por título",
        alias="search",
        min_length=3,
        max_length=50,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$"
    ),
    per_page: int = Query(
        10, ge=1, le=50,
        description="Número de resultados (1-50)"
    ),
    page: int = Query(
        1, ge=1,
        description="Número de página (>=1)"
    ),
    order_by: Literal["id", "title"] = Query(
        "id", description="Campo de orden"
    ),
    direction: Literal["asc", "desc"] = Query(
        "asc", description="Dirección de orden"
    ),
    db: Session = Depends(get_db)
):
    repository = PostRepository(db)
    query = query or text

    total, items = repository.search(
        query, order_by, direction, page, per_page)

    total_pages = math.ceil(total/per_page) if total > 0 else 0
    current_page = 1 if total_pages == 0 else min(page, total_pages)

    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPost(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items
    )


@router.get('/by-tags', response_model=List[PostPublic]) 
def filter_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=1,
        description='Uno o más etiquetas. Ejemplo: ?tags=python&tags=fastapi'
    ),
    db: Session = Depends(get_db)
):
    repository = PostRepository(db=db)
    return repository.by_tags(tag_names=tags)


@router.get(
        '/{post_id}', 
        response_model=Union[PostPublic, PostSummary], 
        response_description='Post encontrado'
) 
def get_post(
    post_id: Annotated[
        int,
        Path(
            ge=1,
            title="ID del post",
            description="Identificador entero del post. Debe ser mayor que 0",
            example=1,
        ),
    ],
    include_content: bool = Query(default=True, description='Include post content'),
    db: Session = Depends(get_db)
):  
    repository = PostRepository(db)
    post = repository.get(post_id=post_id)

    if not post:
        raise HTTPException(status_code=404, detail='Post no encontrado')
    
    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)
    
    return PostSummary.model_validate(post, from_attributes=True)


@router.post("", response_model=PostPublic, response_description="Post creado (OK)", status_code=status.HTTP_201_CREATED)
def create_post(post: Annotated[PostCreate, Depends(PostCreate.as_form)], image: Optional[UploadFile] = File(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = PostRepository(db)
    saved = None
    try:
        if image is not None:
            saved = save_uploaded_image(image)

        image_url = saved["url"] if saved else None

        post = repository.create_post(
            title=post.title,
            content=post.content,
            author=user,
            category_id=post.category_id,
            tags=[tag.model_dump() for tag in post.tags],
            image_url=image_url,
        )
        db.commit()
        db.refresh(post)
        return post
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El título ya existe, prueba con otro")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")
    

@router.put(
        '/{post_id}', 
        response_model=PostPublic, 
        response_description='Post actualizado', 
        response_model_exclude_none=True
)
def update_post(
    post_id: int, 
    data: PostUpdate,
    _editor: UserORM = Depends(require_editor),
    db: Session = Depends(get_db)
):
    repository = PostRepository(db=db)

    post = repository.get(post_id=post_id)

    if not post:
        raise HTTPException(status_code=404, detail='Post no encontrado')
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        post = repository.update_post(post=post, updates=update_data)

        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError:        
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail='Error al actualizar el post'
        )
    
@router.get('/post/slug', response_model=Union[PostPublic, PostSummary])
def get_post_by_slug(slug: str, include_content: bool, db: Session = Depends(get_db)):
    repository = PostRepository(db=db)
    post = repository.get_by_slug(slug=slug)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Post no encontrado'
        )
    
    if include_content:
        return PostSummary.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@router.delete(
        '/{post_id}', 
        status_code=204
)
def delete_post(
    post_id: int,
    _admin: UserORM = Depends(require_admin),
    db: Session = Depends(get_db)
): 
    repository = PostRepository(db=db)

    post = repository.get(post_id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Post no encontrado'
        )
    
    try:     
        repository.delete_post(post=post)        
        db.commit()
        
    except SQLAlchemyError:        
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail='Error al eliminar el post'
        )
    

@router.get('/secure')
def secure_endpoint(
    token: str = Depends(oauth2_scheme)
):
    return {'message': 'Accesso con token', 'token_recibido': token}