import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Request
from sqlmodel import func, select

from db import SessionDep
from models.error import Error
from models.user import (
    MeUpdate,
    User,
    UserCreate,
    UserLogin,
    UserRead,
    UserUpdate,
    UsersRead,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(User.is_admin)])
def read_users(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> UsersRead:
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    total = session.exec(select(func.count(User.id))).one()
    return UsersRead(users=users, total=total)


@router.put("/", dependencies=[Depends(User.is_admin)])
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


@router.get("/{user_id}", dependencies=[Depends(User.is_admin)])
def read_user(user_id: uuid.UUID, session: SessionDep) -> UserRead | Error:
    try:
        user = session.get(User, user_id)
        if not user:
            return Error(message="用户不存在")
        return user
    except Exception as e:
        return Error(message=str(e))


@router.patch("/{user_id}", dependencies=[Depends(User.is_admin)])
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


@router.delete("/{user_id}", dependencies=[Depends(User.is_admin)])
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
def login(request: Request, login: UserLogin, session: SessionDep) -> UserRead | Error:
    try:
        user = session.exec(select(User).where(User.username == login.username)).first()
        if not user:
            return Error(message="用户名或密码错误")
        try:
            PasswordHasher().verify(user.password, login.password)
        except VerifyMismatchError:
            return Error(message="用户名或密码错误")
        request.session["uid"] = user.id.hex
        return user
    except Exception as e:
        return Error(message=str(e))


@router.post("/logout", dependencies=[Depends(User.is_authenticated)])
def logout(request: Request) -> None:
    request.session.clear()


@router.get("/me", dependencies=[Depends(User.is_authenticated)])
def read_me(request: Request, session: SessionDep) -> UserRead | Error:
    try:
        user = User.is_authenticated(request, session)
        return user
    except Exception as e:
        return Error(message=str(e))


@router.post("/me", dependencies=[Depends(User.is_authenticated)])
def update_me(
    request: Request, user: MeUpdate, session: SessionDep
) -> UserRead | Error:
    try:
        db_user = User.is_authenticated(request, session)
        try:
            PasswordHasher().verify(db_user.password, user.old_password)
        except VerifyMismatchError:
            return Error(message="旧密码错误")
        db_user.password = PasswordHasher().hash(user.new_password)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except Exception as e:
        return Error(message=str(e))
