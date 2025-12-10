from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


# ==========================================================
# USER SCHEMAS
# ==========================================================

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone_number: str
    rating: float
    created_at: date

    class Config:
        orm_mode = True


class MessageResponse(BaseModel):
    message: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    password: str
    rating: Optional[float] = 0.0


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    rating: Optional[float] = None


# ==========================================================
# DRIVER SCHEMAS
# ==========================================================

class DriverCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    password: str
    rating: Optional[float] = 0.0
    license: str
    experience_years: Optional[int] = 0


class DriverUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    password: Optional[str]
    license: Optional[str]
    experience_years: Optional[int]
    rating: Optional[float]

    class Config:
        orm_mode = True


class DriverResponse(BaseModel):
    driver_id: int
    license: str
    experience_years: Optional[int] = 0
    user: UserResponse

    class Config:
        orm_mode = True


# ==========================================================
# VEHICLE SCHEMAS
# ==========================================================

class VehicleCreate(BaseModel):
    driver_id: int
    vehicle_type: str
    registration_number: str
    model: str
    color: str
    capacity: int
    insurance_valid_till: date


class VehicleUpdate(BaseModel):
    vehicle_type: Optional[str] = None
    registration_number: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    capacity: Optional[int] = None
    insurance_valid_till: Optional[date] = None


class VehicleResponse(BaseModel):
    vehicle_id: int
    driver_id: int
    vehicle_type: str
    registration_number: str
    model: str
    color: str
    capacity: int
    insurance_valid_till: date

    class Config:
        orm_mode = True


# ==========================================================
# BOOKING SCHEMAS
# ==========================================================

class BookingCreate(BaseModel):
    user_id: int
    pickup_location: str
    dropoff_location: str
    pickup_time: datetime
    fare_estimate: float = 0.0


class BookingResponse(BaseModel):
    booking_id: int
    user_id: int
    driver_id: Optional[int]
    pickup_location: str
    dropoff_location: str
    pickup_time: datetime
    dropoff_time: Optional[datetime] = None
    fare_estimate: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


# ✅ Summary schema for embedding into RideResponse
class BookingSummary(BaseModel):
    booking_id: int
    pickup_location: str
    dropoff_location: str
    pickup_time: datetime
    dropoff_time: Optional[datetime] = None
    fare_estimate: Optional[float] = None
    status: str

    class Config:
        orm_mode = True

class BookingInRide(BaseModel):
    booking_id: Optional[int]
    pickup_location: Optional[str]
    dropoff_location: Optional[str]
    status: Optional[str]

    class Config:
        orm_mode = True

# ----------------------------
# RIDE
# ----------------------------
class RideBase(BaseModel):
    ride_id: int
    user_id: Optional[int]
    driver_id: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    final_fare: Optional[float]
    feedback: Optional[str]
    rating_by_user: Optional[int]
    rating_by_driver: Optional[int]

    class Config:
        orm_mode = True


class RideResponse(RideBase):
    booking: Optional[BookingInRide] = None


class RideCreate(BaseModel):
    user_id: int
    driver_id: int
    booking_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_fare: Optional[float] = None
    feedback: Optional[str] = None

# ==========================================================
# PAYMENT SCHEMAS
# ==========================================================

class PaymentCreate(BaseModel):
    booking_id: int
    amount: float
    payment_method: str
    transaction_id: str
    status: str = "pending"


class PaymentResponse(BaseModel):
    payment_id: int
    booking_id: int
    user_id: Optional[int]
    amount: float
    payment_method: str
    transaction_id: str
    status: str
    timestamp: datetime
    ride_id: Optional[int] = None  # ✅ add this

    class Config:
        orm_mode = True


class PaymentCompleteRequest(BaseModel):
    payment_method: str
    amount: float


# ==========================================================
# COMPLAINT SCHEMAS
# ==========================================================

class ComplaintCreate(BaseModel):
    user_id: int
    ride_id: int
    description: str


class ComplaintResponse(BaseModel):
    complaint_id: int
    user_id: int
    ride_id: int
    description: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==========================================================
# AUTH / ACCESS CONTROL
# ==========================================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int

    class Config:
        orm_mode = True


class PermissionBase(BaseModel):
    name: str


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int

    class Config:
        orm_mode = True


# ==========================================================
# COMPOSITE SCHEMAS
# ==========================================================

class BookingWithRideResponse(BaseModel):
    booking: BookingResponse
    ride: Optional[RideResponse]

    class Config:
        orm_mode = True


class UserWithBookingsResponse(BaseModel):
    user: UserResponse
    bookings: List[BookingResponse]

    class Config:
        orm_mode = True


class DriverWithVehiclesResponse(BaseModel):
    driver: DriverResponse
    vehicles: List[VehicleResponse]

    class Config:
        orm_mode = True
