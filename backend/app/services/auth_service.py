from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def register(self, db: Session, request: RegisterRequest) -> User:
        exists = db.scalar(select(User).where(or_(User.username == request.username, User.email == request.email)))
        if exists:
            raise ValueError("用户名或邮箱已存在")
        user = User(username=request.username, email=request.email, password_hash=hash_password(request.password), role="USER")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate(self, db: Session, request: LoginRequest) -> User | None:
        user = db.scalar(select(User).where(User.username == request.username))
        return user if user and verify_password(request.password, user.password_hash) else None
