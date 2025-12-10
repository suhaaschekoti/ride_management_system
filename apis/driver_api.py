from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from passlib.hash import bcrypt
from sqlalchemy import func
from database import get_db
from models import Driver, Vehicle, Payment, User,Ride
from schemas import (
    DriverCreate,
    DriverResponse,
    DriverUpdate,
    VehicleResponse,
    PaymentResponse,
)
from utils import get_current_user, require_permission, hash_password

router = APIRouter(prefix="/drivers", tags=["Drivers"])


# ✅ Create a new driver (includes user creation)
@router.post("/", response_model=DriverResponse)
def create_driver(driver_data: DriverCreate, db: Session = Depends(get_db)):
    # 1️⃣ Create user entry
    new_user = User(
        name=driver_data.name,
        email=driver_data.email,
        phone_number=driver_data.phone_number,
        password=hash_password(driver_data.password),
        created_at=date.today(),
        role_id=2,  # 🚗 driver role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 2️⃣ Create driver extension
    new_driver = Driver(
        user_id=new_user.user_id,
        license=driver_data.license,
        experience_years=driver_data.experience_years or 0,
    )
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver

@router.get("/by_user/{user_id}", response_model=DriverResponse)
def get_driver_by_user_id(user_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


# ✅ Get a specific driver (Admin or the driver themselves)
@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Admins can view any; drivers can view their own record
    try:
        _ = require_permission("view_all_drivers")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view this driver")

    return driver

@router.get("/{driver_id}/dashboard")
def get_driver_dashboard(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    # 🧠 Only the driver or admin can view this dashboard
    try:
        _ = require_permission("view_all_drivers")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this dashboard")

    # 📊 Dashboard data
    total_rides = db.query(Ride).filter(Ride.driver_id == driver.driver_id).count()
    completed_rides = db.query(Ride).filter(
        Ride.driver_id == driver.driver_id, Ride.end_time.isnot(None)
    ).count()
    total_earnings = (
        db.query(func.sum(Ride.final_fare))
        .filter(Ride.driver_id == driver.driver_id)
        .scalar()
        or 0
    )
    avg_rating = (
        db.query(func.avg(Ride.rating_by_user))
        .filter(Ride.driver_id == driver.driver_id)
        .scalar()
        or 0
    )

    recent_rides = (
        db.query(Ride)
        .filter(Ride.driver_id == driver.driver_id)
        .order_by(Ride.start_time.desc())
        .limit(5)
        .all()
    )

    return {
        "driver_id": driver.driver_id,
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "total_earnings": total_earnings,
        "avg_rating": round(avg_rating, 1),
        "recent_rides": [
            {
                "ride_id": r.ride_id,
                "pickup": r.booking.pickup_location if r.booking else None,
                "dropoff": r.booking.dropoff_location if r.booking else None,
                "status": r.booking.status if r.booking else "unknown",
            }
            for r in recent_rides
        ],
    }


# ✅ Get all drivers (Admin only)
@router.get("/", response_model=List[DriverResponse])
def get_all_drivers(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_drivers")),
):
    return db.query(Driver).all()


# ✅ Update driver (Admin or driver themselves)
@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        _ = require_permission("update_driver")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to update this driver")

    # Update driver or user fields
    for key, value in data.dict(exclude_unset=True).items():
        if key == "password":
            value = bcrypt.hash(value)
            setattr(driver.user, key, value)
        elif hasattr(driver, key):
            setattr(driver, key, value)
        elif hasattr(driver.user, key):
            setattr(driver.user, key, value)

    db.commit()
    db.refresh(driver)
    return driver


# ✅ Partial update (Admin or driver themselves)
@router.patch("/{driver_id}", response_model=DriverResponse)
def partial_update_driver(
    driver_id: int,
    data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        _ = require_permission("update_driver")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to modify this driver")

    for key, value in data.dict(exclude_unset=True).items():
        if key == "password":
            value = bcrypt.hash(value)
            setattr(driver.user, key, value)
        elif hasattr(driver, key):
            setattr(driver, key, value)
        elif hasattr(driver.user, key):
            setattr(driver.user, key, value)

    db.commit()
    db.refresh(driver)
    return driver


# ✅ Delete driver (Admin or the driver themselves)
@router.delete("/{driver_id}", status_code=status.HTTP_200_OK)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        _ = require_permission("delete_driver")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this driver")

    driver_name = driver.user.name
    db.delete(driver)
    db.commit()
    return {"message": f"Driver '{driver_name}' deleted successfully"}


# ✅ View vehicle details (Admin or that driver)
@router.get("/{driver_id}/vehicles", response_model=List[VehicleResponse])
def view_driver_vehicles(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        _ = require_permission("view_driver_vehicles")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view these vehicles")

    vehicles = db.query(Vehicle).filter(Vehicle.driver_id == driver_id).all()
    return vehicles


# ✅ View payments (Admin or that driver)
@router.get("/{driver_id}/payments", response_model=List[PaymentResponse])
def view_driver_payments(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        _ = require_permission("view_driver_payments")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and driver.user.email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view these payments")

    payments = (
        db.query(Payment)
        .join(Payment.booking)
        .filter(Payment.booking.has(driver_id=driver_id))
        .all()
    )
    return payments
