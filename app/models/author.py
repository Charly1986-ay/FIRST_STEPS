from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from typing import List, TYPE_CHECKING
from app.core.db import Base

if TYPE_CHECKING:
    from .post import PostORM

class AuthorORM(Base):
    __tablename__= "authors"    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  
    # relacion de 1 a n
    #posts: Mapped[List['PostORM']] = relationship(back_populates="author")
    posts: Mapped[List["PostORM"]] = relationship(
        "PostORM",
        back_populates="author"
    )