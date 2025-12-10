from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Role
from schemas import RoleCreate, RoleResponse
from utils import require_permission

router = APIRouter(prefix="/roles", tags=["Roles"])


# ✅ CREATE ROLE (Admin only)
@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Allows admin to create a new role in the system."
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("create_role"))
):
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = Role(name=role_data.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


# ✅ GET ALL ROLES (Admin only)
@router.get(
    "/",
    response_model=List[RoleResponse],
    summary="Get all roles",
    description="Returns a list of all roles. Only accessible to admins."
)
def get_roles(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_roles"))
):
    return db.query(Role).all()


# ✅ GET ROLE BY ID (Admin only)
@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get a specific role by ID",
    description="Admin can view role details by ID."
)
def get_role_by_id(
    role_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_roles"))
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# ✅ DELETE ROLE (Admin only)
@router.delete(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a role",
    description="Admin can delete a role. This will also delete related role-permission mappings."
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("delete_role"))
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return {"message": f"Role '{role.name}' deleted successfully"}
