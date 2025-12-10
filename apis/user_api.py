from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List

from database import get_db
from models import User, Role
from schemas import UserCreate, UserResponse, UserUpdate
from fastapi.security import OAuth2PasswordRequestForm
from utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_permission,
    oauth2_scheme
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/users", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password=hash_password(user_data.password),
        created_at=date.today(),
        role_id=3  # 👤 rider role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    # get_current_user already loads and validates user from token
    # return the SQLAlchemy user object (UserResponse will read fields via orm_mode)
    return current_user


# ✅ GET ALL USERS (Admin only)
@router.get("/", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_user"))
):
    return db.query(User).all()


# ✅ GET SINGLE USER (Self or Admin)
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Allow if admin or self
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or (role.name.lower() != "admin" and current_user.user_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return user


# ✅ UPDATE USER (Self or Admin)
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated_user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: str = Depends(require_permission("update_user"))
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or (role.name.lower() != "admin" and current_user.user_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    user.name = updated_user.name
    user.email = updated_user.email
    user.phone_number = updated_user.phone_number
    user.password = hash_password(updated_user.password)
    user.rating = updated_user.rating or user.rating

    db.commit()
    db.refresh(user)
    return user


# ✅ PARTIAL UPDATE USER (Self or Admin)
@router.patch("/{user_id}", response_model=UserResponse)
def partial_update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: str = Depends(require_permission("update_user"))
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or (role.name.lower() != "admin" and current_user.user_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    data = user_update.dict(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    for k, v in data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return user


# ✅ DELETE USER (Admin or self)
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: str = Depends(require_permission("delete_user"))
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or (role.name.lower() != "admin" and current_user.user_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    db.delete(user)
    db.commit()
    return {"message": f"User '{user.name}' deleted successfully."}


# ✅ LOGIN
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token_expires = timedelta(hours=1)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# ✅ LOGOUT (No permission needed)
@router.post("/logout")
def logout_user(_: str = Depends(oauth2_scheme)):
    return {"message": "User logged out successfully"}
