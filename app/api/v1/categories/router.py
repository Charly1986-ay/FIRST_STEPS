from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.categories.repository import CategoryRepository
from app.core.db import get_db
from app.api.v1.categories.schemas import CategoryCreate, CategoryUpdate, CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryPublic])
def list_categories(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    return repository.list_many(skip=skip, limit=limit)


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)

    if repository.get_by_slug(slug=data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='El slug ya existe'
        )    
    category = repository.create(name=data.name, slug=data.slug)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No existe la categoría'
        )
    return category


@router.put("/{category_id}", response_model=CategoryPublic)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No existe la categoría'
        )
    updated = repository.update(
        category=category, 
        # model_dump => convierte un modelo pydantic a diccionario, 
        # la propiedad exclude_unset hace la conversion con los datos enviados por el usuario
        updates=data.model_dump(exclude_unset=True)
    )
    db.commit()
    db.refresh(updated)
    return updated

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)

    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No existe la categoría'
        )
    repository.delete(category=category)