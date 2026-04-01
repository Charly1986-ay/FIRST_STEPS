from contextlib import contextmanager
import email
from typing import Optional

from pydantic import Tag
from sqlalchemy import select
from sqlalchemy.orm import Session

from pwdlib import PasswordHash

from app.core.db import SessionLocal
from app.models.category import CategoryORM
from app.models.tag import TagORM
from app.models.user import UserORM
from app.seeds.data.categories import CATEGORIES
from app.seeds.data.tags import TAGS
from app.seeds.data.user import USERS


def hash_password(plain: str) -> str:
    return PasswordHash.recommended().hash(plain)

# el contextmanager asegura que se ejecute al inicio al final 
# aunque tenga errores
@contextmanager
def atomic(db: Session):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise

def _user_by_email(db: Session, email: str) -> Optional[UserORM]:
    return db.execute(select(UserORM).where(UserORM.email==email)).scalars().first()

def _category_by_slug(db: Session, slug: str) -> Optional[CategoryORM]:
    return db.execute(select(CategoryORM).where(CategoryORM.slug==slug)).scalars().first()

def _tag_by_name(db: Session, name: str) -> Optional[TagORM]:
    return db.execute(select(TagORM).where(TagORM.name==name)).scalars().first()

def seed_users(db: Session) -> None:
    with atomic(db=db):
        for data in USERS:
            obj = _user_by_email(db=db, email=data['email'])
            if obj:
                changed = False
                if obj.full_name != data.get('full_name'):
                    obj.full_name = data.get('full_name')
                    changed = True
                if data.get('password'):
                    obj.hash_password = hash_password(data.get('password'))
                    changed = True
                if data.get('rol'):
                    obj.role = data.get('rol')
                    changed = True
                if changed:
                    db.add(obj)
            else:
                db.add(UserORM(
                    email = data['email'],
                    full_name = data.get('full_name'),
                    hash_password = hash_password(data.get('password')),
                    role = data.get('role')
                ))


def seed_categories(db: Session) -> None:
    with atomic(db=db):
        for data in CATEGORIES:
            obj = _category_by_slug(db=db, slug=data['slug'])
            if obj:                
                if obj.name != data.get('name'):
                    obj.name = data.get('name') 
                    db.add(obj)  
            else:
                db.add(CategoryORM(
                    name = data.get('name'),
                    slug = data['slug']
                ))  


def seed_tags(db: Session) -> None:
    with atomic(db=db):
        for data in TAGS:
            obj = _tag_by_name(db=db, name=data['name'])
            if obj:
                if obj.name != data.get('name'):
                    obj.name = data.get('name')   
            else:
                db.add(TagORM(name = data.get('name')))  


def run_all() -> None:
    with SessionLocal() as db:    
        seed_users(db)
        seed_categories(db) 
        seed_tags(db)   

def run_users() -> None:
    with SessionLocal() as db:
        seed_users(db)   

def run_categories() -> None:
    with SessionLocal() as db:
        seed_categories(db)      

def run_tags() -> None:
    with SessionLocal() as db:
        seed_tags(db)   