from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Ride, Role, User, Driver
from schemas import RideResponse, RideCreate
from utils import get_current_user, require_permission

router = APIRouter(prefix="/rides", tags=["Rides"])


# ✅ CREATE RIDE (Admin only)
@router.post(
    "/",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a ride (Admin only)",
    description="Admin can manually create a ride record — usually for testing or data correction."
)
def create_ride(
    ride_data: RideCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("create_ride"))
):
    new_ride = Ride(**ride_data.dict())
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    return new_ride


# ✅ GET RIDE BY ID (Admin, Driver in ride, or User in ride)
@router.get(
    "/{ride_id}",
    response_model=RideResponse,
    summary="Get ride details",
    description="Admin, driver, or the user involved in the ride can view ride details."
)
def get_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_admin = role and role.name.lower() == "admin"

    # Only admin, driver of the ride, or user of the ride can view
    if not is_admin and current_user.user_id not in [ride.user_id]:
        driver = db.query(Driver).filter(Driver.driver_id == ride.driver_id).first()
        if not driver or driver.email != current_user.email:
            raise HTTPException(status_code=403, detail="Not authorized to view this ride")

    return ride


# ✅ GET ALL RIDES (Admin only)
@router.get(
    "/",
    response_model=List[RideResponse],
    summary="View all rides (Admin only)",
    description="Lists all rides in the system. Only admins can access this."
)
def get_all_rides(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_rides"))
):
    return db.query(Ride).all()


# ✅ GET RIDES BY USER (with booking status)
@router.get(
    "/user/{user_id}",
    response_model=List[RideResponse],
    summary="Get rides for a specific user (with booking status)",
    description="Returns all rides for a user, including booking status. Admins can view any user's rides."
)
def get_rides_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Permission check
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_admin = role and role.name.lower() == "admin"

    if not is_admin and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' rides")

    # Joined load to include booking info
    rides = (
        db.query(Ride)
        .options(joinedload(Ride.booking))
        .filter(Ride.user_id == user_id)
        .all()
    )
    return rides


@router.get(
    "/driver/{driver_id}",
    response_model=List[RideResponse],
    summary="Get rides handled by a driver",
    description="Driver can see their own rides; Admin can view all driver rides."
)
def get_rides_by_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # ✅ Fix email access
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_admin = role and role.name.lower() == "admin"

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view these rides")

    # ✅ JOIN BOOKINGS to include pickup/dropoff
    rides = (
        db.query(Ride)
        .options(joinedload(Ride.booking))
        .filter(Ride.driver_id == driver_id)
        .all()
    )

    return rides

# ✅ UPDATE RIDE FEEDBACK & RATINGS (User or Driver)
@router.put(
    "/{ride_id}/feedback",
    response_model=RideResponse,
    summary="Update ride feedback",
    description="Allows driver and user to give ratings and feedback after the ride ends."
)
def update_ride_feedback(
    ride_id: int,
    user_rating: Optional[int] = None,
    driver_rating: Optional[int] = None,
    user_feedback: Optional[str] = None,
    driver_feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    # User feedback
    if current_user.user_id == ride.user_id:
        if user_rating is not None:
            ride.rating_by_user = user_rating
        if user_feedback:
            ride.feedback = (ride.feedback or "") + f"\n[User]: {user_feedback}"

    # Driver feedback
    elif role and role.name.lower() == "driver":
        driver = db.query(Driver).filter(Driver.driver_id == ride.driver_id).first()
        if not driver or driver.email != current_user.email:
            raise HTTPException(status_code=403, detail="Not authorized to update this feedback")
        if driver_rating is not None:
            ride.rating_by_driver = driver_rating
        if driver_feedback:
            ride.feedback = (ride.feedback or "") + f"\n[Driver]: {driver_feedback}"

    else:
        raise HTTPException(status_code=403, detail="Not authorized to update feedback")

    db.commit()
    db.refresh(ride)
    return ride


# ✅ DELETE RIDE (Admin only)
@router.delete(
    "/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a ride record (Admin only)",
    description="Admin can delete any ride record for maintenance or cleanup."
)
def delete_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("delete_ride"))
):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    db.delete(ride)
    db.commit()
    return {"message": "Ride deleted successfully"}

