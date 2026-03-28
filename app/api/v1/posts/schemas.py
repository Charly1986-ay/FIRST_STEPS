from ast import AnnAssign

from fastapi import Form
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Annotated, List, Optional, Literal

from app.api.v1.auth.schemas import UserPublic
from app.api.v1.categories.schemas import CategoryPublic

class Author(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description='Nombre del autor'
        )
    email: EmailStr
    model_config = ConfigDict(from_attributes=True) 


class Tag(BaseModel):    
    name: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description='Nombre de la etiqueta'
    )   
    model_config = ConfigDict(from_attributes=True) 

class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list)  # []
    user: Optional[UserPublic] = None
    image_url: Optional[str] = None
    category: Optional[CategoryPublic] = None

    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Titulo del post (mínimo 3 caracteres, máximo 100)",
        examples=["Mi primer post con FastAPI"]
    )
    content: Optional[str] = Field(
        default="Contenido no disponible",
        min_length=10,
        description="Contenido del post (mínimo 10 caracteres)",
        examples=["Este es un contenido válido porque tiene 10 caracteres o más"]
    )
    category_id: Optional[int] = None
    tags: List[Tag] = Field(default_factory=list)  # []
    # author: Optional[Author] = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        if "spam" in value.lower():
            raise ValueError("El título no puede contener la palabra: 'spam'")
        return value

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        category_id: Annotated[int, Form(ge=1)],
        tags: Annotated[Optional[List[str]], Form()] = None,
    ):
        tag_objs = []

        for t in (tags or []):
            parts = t.split(",")

            for p in parts:
                name = p.strip()
                if name:
                    tag_objs.append(Tag(name=name))
        return cls(title=title, content=content, category_id=category_id, tags=tag_objs)
    

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None

class PostPublic(PostBase):
    id: int    

    # ConfigDict es una configuración que recibe un sqlalchemy y lo convierte JSON
    model_config = ConfigDict(from_attributes=True)

class PostSummary(BaseModel):
    id: int
    title: str  

    model_config = ConfigDict(from_attributes=True)

class PaginatedPost(BaseModel):
    page:int
    per_page: int
    total: int   
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal['id', 'title']
    direction: Literal['asc', 'desc']
    search: Optional[str] = None
    items: List[PostPublic]