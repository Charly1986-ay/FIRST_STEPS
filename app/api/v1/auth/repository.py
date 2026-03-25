from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserORM

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> UserORM | None:
        return self.db.get(UserORM, user_id)
    
    def get_by_email(self, email: str) -> UserORM | None:
        query = select(UserORM).where(UserORM.email==email)
        return self.db.execute(query).scalar_one_or_none()
    
    def create(self, email: str, hashed_password: str, full_name: str | None) -> UserORM:
        user = UserORM(
            email=email, 
            hash_password=hashed_password, 
            full_name=full_name
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
    
    def set_role(self, user: UserORM, role: str) -> UserORM:
        user.role = role
        self.db.add(user) 
        self.db.flush()       
        self.db.refresh(user)
        return user