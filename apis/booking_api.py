from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Booking, Ride, Payment, Role, User, Driver
from schemas import BookingCreate, BookingResponse, PaymentResponse
from utils import get_current_user, require_permission

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# ✅ 1️⃣ Create Booking (User)
@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("create_booking")),
):
    if current_user.user_id != booking_data.user_id:
        raise HTTPException(status_code=403, detail="You can only create bookings for yourself")

    new_booking = Booking(
        user_id=booking_data.user_id,
        pickup_location=booking_data.pickup_location,
        dropoff_location=booking_data.dropoff_location,
        pickup_time=booking_data.pickup_time,
        fare_estimate=booking_data.fare_estimate,
        status="requested",
        created_at=datetime.utcnow()
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

# ✅ 4️⃣ View Available Bookings (Drivers)
@router.get("/available", response_model=List[BookingResponse])
def get_available_bookings(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_available_bookings")),
):
    return db.query(Booking).filter(Booking.status == "requested").all()

# ✅ 2️⃣ Get Booking by ID
@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check if user has admin permission
    try:
        _ = require_permission("view_all_bookings")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and booking.user_id != current_user.user_id:
        driver = db.query(Driver).join(User).filter(User.user_id == current_user.user_id).first()
        if not driver or booking.driver_id != driver.driver_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this booking")

    return booking


# ✅ 3️⃣ Get All Bookings (Admin)
@router.get("/", response_model=List[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_bookings")),
):
    return db.query(Booking).all()




# ✅ 5️⃣ Driver Accepts Booking & Proposes Fare
@router.put("/{booking_id}/accept", response_model=BookingResponse)
def accept_booking_with_fare(
    booking_id: int,
    proposed_fare: float,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("accept_booking")),
):
    driver = db.query(Driver).join(User).filter(User.user_id == current_user.user_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    booking = db.query(Booking).filter(Booking.booking_id == booking_id, Booking.status == "requested").first()
    if not booking:
        raise HTTPException(status_code=400, detail="Booking not available")

    try:
        booking.driver_id = driver.driver_id
        booking.status = "pending_user_confirmation"
        booking.fare_estimate = proposed_fare
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking already accepted by another driver")

    return booking


# ✅ 6️⃣ User Confirms Fare
@router.put("/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking_fare(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("confirm_booking")),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only confirm your own bookings")

    if booking.status != "pending_user_confirmation":
        raise HTTPException(status_code=400, detail="Booking not awaiting confirmation")

    booking.status = "accepted"
    db.commit()
    db.refresh(booking)
    return booking


# ✅ 7️⃣ Driver Views Accepted Bookings
@router.get("/driver/{driver_id}/accepted", response_model=List[BookingResponse])
def accepted_bookings_for_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_driver_bookings")),
):
    return db.query(Booking).filter(Booking.driver_id == driver_id, Booking.status == "accepted").all()


# ✅ 8️⃣ Cancel Booking
@router.put("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: str = Depends(require_permission("cancel_booking")),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status in ["completed", "paid"]:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed or paid booking")

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking


# ✅ 9️⃣ Start Ride (Driver)
@router.put("/{booking_id}/start", response_model=BookingResponse)
def start_ride(
    booking_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("start_ride")),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking or booking.status != "accepted":
        raise HTTPException(status_code=400, detail="Booking not ready to start")

    booking.status = "ongoing"
    new_ride = Ride(
        booking_id=booking.booking_id,
        user_id=booking.user_id,
        driver_id=booking.driver_id,
        start_time=datetime.utcnow(),
        distance_travelled=0,
        final_fare=booking.fare_estimate,
    )
    db.add(new_ride)
    db.commit()
    db.refresh(booking)
    return booking


# ✅ 🔟 End Ride (Driver)
@router.put("/{booking_id}/end", response_model=BookingResponse)
def end_ride(
    booking_id: int,
    user_rating: Optional[int] = None,
    driver_rating: Optional[int] = None,
    user_feedback: Optional[str] = None,
    driver_feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("end_ride_with_rating")),
):
    ride = db.query(Ride).filter(Ride.booking_id == booking_id).first()
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()

    if not booking or not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    ride.end_time = datetime.utcnow()
    booking.status = "completed"

    if user_rating is not None:
        ride.rating_by_user = user_rating
        if user_feedback:
            ride.feedback = (ride.feedback or "") + f"\n[User]: {user_feedback}"
    if driver_rating is not None:
        ride.rating_by_driver = driver_rating
        if driver_feedback:
            ride.feedback = (ride.feedback or "") + f"\n[Driver]: {driver_feedback}"

    driver = db.query(Driver).filter(Driver.driver_id == booking.driver_id).first()
    user = db.query(User).filter(User.user_id == booking.user_id).first()
    db.commit()

    # ✅ Update average ratings
    if driver:
        all_driver_rides = db.query(Ride).filter(Ride.driver_id == driver.driver_id, Ride.rating_by_user.isnot(None)).all()
        if all_driver_rides:
            driver.user.rating = sum(r.rating_by_user for r in all_driver_rides) / len(all_driver_rides)

    if user:
        all_user_rides = db.query(Ride).filter(Ride.user_id == user.user_id, Ride.rating_by_driver.isnot(None)).all()
        if all_user_rides:
            user.rating = sum(r.rating_by_driver for r in all_user_rides) / len(all_user_rides)

    # ✅ Generate Payment (added user_id!)
    if not db.query(Payment).filter(Payment.booking_id == booking.booking_id).first():
        payment = Payment(
            booking_id=booking.booking_id,
            user_id=booking.user_id,  # ✅ Fix: added user_id
            amount=booking.fare_estimate,
            payment_method="cash",
            transaction_id=f"TXN-{booking.booking_id}-{int(datetime.utcnow().timestamp())}",
            status="pending",
            timestamp=datetime.utcnow(),
        )
        db.add(payment)

    db.commit()
    db.refresh(booking)
    return booking


# ✅ 11️⃣ View Payment
@router.get("/{booking_id}/payment", response_model=PaymentResponse)
def view_payment(
    booking_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_payment")),
):
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ✅ 12️⃣ Complete Payment
@router.put("/{booking_id}/pay", response_model=PaymentResponse)
def complete_payment(
    booking_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("complete_payment")),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record missing")

    if booking.status not in ["completed", "paid"]:
        raise HTTPException(status_code=400, detail="Ride must be completed before payment")

    if payment.status == "completed":
        raise HTTPException(status_code=400, detail="Payment already completed")

    payment.status = "completed"
    booking.status = "paid"
    payment.timestamp = datetime.utcnow()

    db.commit()
    db.refresh(payment)
    return payment


# ✅ 13️⃣ Filtered Listings
# ✅ Allow logged-in user to see their own bookings
@router.get("/user/me", response_model=List[BookingResponse])
def my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Booking).filter(Booking.user_id == current_user.user_id).all()


@router.get("/user/{user_id}", response_model=List[BookingResponse])
def bookings_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_user_bookings")),
):
    return db.query(Booking).filter(Booking.user_id == user_id).all()


@router.get("/driver/{driver_id}", response_model=List[BookingResponse])
def bookings_by_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_driver_bookings")),
):
    return db.query(Booking).filter(Booking.driver_id == driver_id).all()


@router.get("/ongoing", response_model=List[BookingResponse])
def ongoing_bookings(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_bookings")),
):
    return db.query(Booking).filter(Booking.status == "ongoing").all()


@router.get("/completed", response_model=List[BookingResponse])
def completed_bookings(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_bookings")),
):
    return db.query(Booking).filter(Booking.status == "completed").all()
