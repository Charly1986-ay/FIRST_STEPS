from datetime import datetime
from typing import List, Literal

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.post import PostORM

Role = Literal['user', 'editor', 'admin']

class UserORM(Base):
    __tablename__= "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False) 
    hash_password: Mapped[str] = mapped_column(
        String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum('user', 'editor', 'admin', name='role_enum'), default='user')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    create_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    
    posts: Mapped[List["PostORM"]] = relationship(
        "PostORM",
        back_populates="user"
    )