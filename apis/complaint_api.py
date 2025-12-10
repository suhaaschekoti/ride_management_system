from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from database import get_db
from models import Complaint, Ride
from schemas import ComplaintCreate, ComplaintResponse
from utils import get_current_user, require_permission

router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ✅ 1️⃣ Create Complaint (User only)
@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("create_complaint")),
):
    # Ensure the user creates a complaint for their own ride
    if current_user.user_id != complaint_data.user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only file complaints for your own rides",
        )

    # Check that the ride exists
    ride = db.query(Ride).filter(Ride.ride_id == complaint_data.ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    new_complaint = Complaint(
        user_id=complaint_data.user_id,
        ride_id=complaint_data.ride_id,
        description=complaint_data.description,
        status="open",
        created_at=datetime.utcnow(),
        resolved_at=None,
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return new_complaint


# ✅ 2️⃣ Get Complaint by ID (Admin or Complaint Owner)
@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Admins have view_all_complaints permission
    try:
        _ = require_permission("view_all_complaints")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and complaint.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this complaint")

    return complaint


# ✅ 3️⃣ Get All Complaints (Admin only)
@router.get("/", response_model=List[ComplaintResponse])
def get_all_complaints(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_complaints")),
):
    return db.query(Complaint).all()


# ✅ 4️⃣ Get Complaints by User (User or Admin)
@router.get("/user/{user_id}", response_model=List[ComplaintResponse])
def get_complaints_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Allow admin (with view_all_complaints) or self
    try:
        _ = require_permission("view_all_complaints")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these complaints")

    return db.query(Complaint).filter(Complaint.user_id == user_id).all()


# ✅ 5️⃣ Resolve Complaint (Admin only)
@router.put("/{complaint_id}/resolve", response_model=ComplaintResponse)
def resolve_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("resolve_complaint")),
):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.status == "resolved":
        raise HTTPException(status_code=400, detail="Complaint already resolved")

    complaint.status = "resolved"
    complaint.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(complaint)
    return complaint


# ✅ 6️⃣ Delete Complaint (Admin or Complaint Owner)
@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Admins can delete all
    try:
        _ = require_permission("delete_complaint")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and complaint.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this complaint")

    db.delete(complaint)
    db.commit()
    return None
