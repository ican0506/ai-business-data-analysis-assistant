from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
service = AuthService()


def user_to_dict(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise credentials_error

    user = db.get(User, user_id)
    if not user:
        raise credentials_error
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user = service.register(db, request)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return {"code": 0, "message": "注册成功", "data": user_to_dict(user)}


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = service.authenticate(db, request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return {
        "code": 0,
        "message": "登录成功",
        "data": {"access_token": create_access_token(str(user.id)), "token_type": "bearer"},
    }


@router.post("/token", include_in_schema=False)
def swagger_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    """提供给 Swagger OAuth2 授权弹窗使用的标准表单登录接口。"""
    request = LoginRequest(username=form_data.username, password=form_data.password)
    user = service.authenticate(db, request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"code": 0, "message": "查询成功", "data": user_to_dict(current_user)}
