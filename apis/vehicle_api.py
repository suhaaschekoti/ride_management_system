from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Vehicle, Driver, Role, User
from schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from utils import get_current_user, require_permission

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# ✅ CREATE VEHICLE (Driver or Admin)
@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("create_vehicle")),
):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    driver = db.query(Driver).filter(Driver.driver_id == vehicle_data.driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # ✅ Access driver email through related User
    driver_email = driver.user.email

    # Only admin or that specific driver can add a vehicle
    if not role or (role.name.lower() != "admin" and current_user.email != driver_email):
        raise HTTPException(status_code=403, detail="Not authorized to add vehicle")

    new_vehicle = Vehicle(**vehicle_data.dict())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


# ✅ GET VEHICLE BY ID (Admin or the driver who owns it)
@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("view_vehicle")),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view this vehicle")

    return vehicle


# ✅ GET ALL VEHICLES (Admin only)
@router.get("/", response_model=List[VehicleResponse])
def get_all_vehicles(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_vehicles")),
):
    return db.query(Vehicle).all()


# ✅ GET VEHICLES BY DRIVER ID (Admin or that driver)
@router.get("/driver/{driver_id}", response_model=List[VehicleResponse])
def get_vehicles_by_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("view_vehicle")),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view these vehicles")

    vehicles = db.query(Vehicle).filter(Vehicle.driver_id == driver_id).all()
    return vehicles


# ✅ UPDATE VEHICLE (Admin or that driver)
@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("update_vehicle")),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to update this vehicle")

    for key, value in vehicle_data.dict(exclude_unset=True).items():
        setattr(vehicle, key, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


# ✅ DELETE VEHICLE (Admin or that driver)
@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("delete_vehicle")),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this vehicle")

    db.delete(vehicle)
    db.commit()
    return None


# ✅ GET ALL VEHICLES (Admin only)
@router.get("/", response_model=List[VehicleResponse])
def get_all_vehicles(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_vehicles")),
):
    return db.query(Vehicle).all()


# ✅ GET VEHICLES BY DRIVER ID (Admin or that driver)
@router.get("/driver/{driver_id}", response_model=List[VehicleResponse])
def get_vehicles_by_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("view_vehicle")),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view these vehicles")

    vehicles = db.query(Vehicle).filter(Vehicle.driver_id == driver_id).all()
    return vehicles


# ✅ UPDATE VEHICLE (Admin or that driver)
@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("update_vehicle")),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to update this vehicle")

    for key, value in vehicle_data.dict(exclude_unset=True).items():
        setattr(vehicle, key, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


# ✅ DELETE VEHICLE (Admin or that driver)
@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("delete_vehicle")),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    if role.name.lower() != "admin" and current_user.email != driver.user.email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this vehicle")

    db.delete(vehicle)
    db.commit()
    return None
