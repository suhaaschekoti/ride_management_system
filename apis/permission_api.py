from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Permission, RolePermission, Role, User
from schemas import PermissionCreate, PermissionResponse
from utils import require_permission, get_current_user

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# ✅ CREATE PERMISSION (Admin only)
@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("create_permission"))
):
    if db.query(Permission).filter(Permission.name == permission_data.name).first():
        raise HTTPException(status_code=400, detail="Permission already exists")

    new_perm = Permission(name=permission_data.name)
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm


# ✅ GET ALL PERMISSIONS
@router.get("/", response_model=List[PermissionResponse])
def get_permissions(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_permission"))
):
    return db.query(Permission).all()


# ✅ ASSIGN PERMISSIONS TO ROLE (Appends — does NOT delete existing)
@router.post("/assign/{role_id}", status_code=status.HTTP_200_OK)
def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("assign_role_permission"))
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    valid_perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(valid_perms) != len(permission_ids):
        raise HTTPException(status_code=400, detail="Some permission IDs are invalid")

    # ✅ Only add new permissions if not already assigned
    added_count = 0
    for perm in valid_perms:
        exists = db.query(RolePermission).filter_by(role_id=role.id, permission_id=perm.id).first()
        if not exists:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
            added_count += 1

    db.commit()
    return {"message": f"{added_count} new permissions assigned to role '{role.name}'"}


# ✅ DELETE PERMISSION (Admin only)
@router.delete("/{permission_id}", status_code=status.HTTP_200_OK)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a permission and its related role assignments (Admin only)."""

    # ✅ Verify the user has admin role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can delete permissions."
        )

    # 🔍 Check if permission exists
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # 🧹 Delete related RolePermission entries
    db.query(RolePermission).filter(RolePermission.permission_id == permission_id).delete()

    # 🗑️ Delete the permission itself
    db.delete(permission)
    db.commit()

    return {
        "message": f"Permission '{permission.name}' and all related role links deleted successfully."
    }
