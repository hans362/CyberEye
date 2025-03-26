from fastapi import APIRouter
from db import SessionDep
from sqlmodel import select
from models.user import User, UserCreate, UserRead, UserUpdate
from models.error import Error
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import uuid


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def read_users(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> list[UserRead]:
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


@router.put("/")
def create_user(session: SessionDep, user: UserCreate) -> UserRead | Error:
    try:
        if session.exec(select(User).where(User.username == user.username)).first():
            return Error(message="用户名已存在")
        user.password = PasswordHasher().hash(user.password)
        db_user = User.model_validate(user)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except Exception as e:
        return Error(message=str(e))


@router.get("/{user_id}")
def read_user(user_id: uuid.UUID, session: SessionDep) -> UserRead | Error:
    try:
        user = session.get(User, user_id)
        if not user:
            return Error(message="用户不存在")
        return user
    except Exception as e:
        return Error(message=str(e))


@router.patch("/{user_id}")
def update_user(
    user_id: uuid.UUID, user: UserUpdate, session: SessionDep
) -> UserRead | Error:
    try:
        db_user = session.get(User, user_id)
        if not db_user:
            return Error(message="用户不存在")
        if user.username:
            db_user.username = user.username
        if user.password:
            db_user.password = PasswordHasher().hash(user.password)
        if user.role:
            db_user.role = user.role
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except Exception as e:
        return Error(message=str(e))


@router.delete("/{user_id}")
def delete_user(user_id: uuid.UUID, session: SessionDep) -> None | Error:
    try:
        user = session.get(User, user_id)
        if not user:
            return Error(message="用户不存在")
        session.delete(user)
        session.commit()
    except Exception as e:
        return Error(message=str(e))


@router.post("/login")
def login(username: str, password: str, session: SessionDep) -> UserRead | Error:
    try:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            return Error(message="用户名或密码错误")
        try:
            PasswordHasher().verify(user.password, password)
        except VerifyMismatchError:
            return Error(message="用户名或密码错误")
        return user
    except Exception as e:
        return Error(message=str(e))
