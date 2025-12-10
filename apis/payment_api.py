from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import *
from schemas import *
from utils import get_current_user, require_permission

router = APIRouter(prefix="/payments", tags=["Payments"])

# ✅ 10️⃣ Get payments for a driver
@router.get("/driver-payments", response_model=List[PaymentResponse])
def get_payments_for_driver(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find driver for this user
    driver = db.query(Driver).filter(Driver.user_id == current_user.user_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Join Payment → Booking → Ride to get ride_id
    payments = (
        db.query(Payment, Ride.ride_id)
        .join(Booking, Payment.booking_id == Booking.booking_id)
        .join(Ride, Ride.booking_id == Booking.booking_id)
        .filter(Ride.driver_id == driver.driver_id)
        .all()
    )

    if not payments:
        raise HTTPException(status_code=404, detail="No payments found")

    # Build response manually to include ride_id
    response_data = []
    for payment, ride_id in payments:
        payment_data = {
            "payment_id": payment.payment_id,
            "booking_id": payment.booking_id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "timestamp": payment.timestamp,
            "ride_id": ride_id  # ✅ include ride_id
        }
        response_data.append(payment_data)

    return response_data


@router.get("/me/pending", response_model=List[PaymentResponse])
def get_my_pending_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        print(f"[DEBUG] Current user: {current_user.user_id}")
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == current_user.user_id, Payment.status == "pending")
            .all()
        )
        print(f"[DEBUG] Found {len(payments)} payments")
        return payments
    except Exception as e:
        import traceback
        print("[ERROR] Exception in get_my_pending_payments:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching payments: {str(e)}")



# ✅ 2️⃣ User — View My Completed Payments
@router.get("/me/completed", response_model=List[PaymentResponse])
def get_my_completed_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return (
            db.query(Payment)
            .filter(Payment.user_id == current_user.user_id, Payment.status == "completed")
            .all()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payments: {str(e)}")


# ✅ 3️⃣ Get all payments (Admin only)
@router.get("/", response_model=List[PaymentResponse])
def get_all_payments(
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_payments")),
):
    return db.query(Payment).all()


# ✅ 4️⃣ Get payment by ID (Admin or related user/driver)
@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    user_id = getattr(current_user, "user_id", None)
    is_related = user_id in [payment.user_id, payment.driver_id]

    # Check admin permission
    try:
        _ = require_permission("view_all_payments")(current_user, db)
        is_admin = True
    except Exception:
        is_admin = False

    if not is_admin and not is_related:
        raise HTTPException(status_code=403, detail="Not authorized to view this payment")

    return payment


# ✅ 5️⃣ Filter by status (Admin only)
@router.get("/status/{status}", response_model=List[PaymentResponse])
def get_payments_by_status(
    status: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_payments")),
):
    return db.query(Payment).filter(Payment.status == status).all()


# ✅ 6️⃣ Filter by date range (Admin only)
@router.get("/date-range/", response_model=List[PaymentResponse])
def get_payments_by_date_range(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("view_all_payments")),
):
    return (
        db.query(Payment)
        .filter(Payment.timestamp >= start_date, Payment.timestamp <= end_date)
        .all()
    )


# ✅ 7️⃣ Update payment status (Admin only)
@router.put("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("update_payment_status")),
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = new_status
    payment.timestamp = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return payment


# ✅ 8️⃣ Complete a Pending Payment (User)
@router.put("/{payment_id}/complete", response_model=PaymentResponse)
def complete_pending_payment(
    payment_id: int,
    payment_data: PaymentCompleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only complete your own payments")

    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Payment already processed or invalid")

    if round(payment_data.amount, 2) != round(payment.amount, 2):
        raise HTTPException(status_code=400, detail="Payment amount mismatch")

    # ✅ Update
    payment.status = "completed"
    payment.payment_method = payment_data.payment_method
    payment.timestamp = datetime.utcnow()

    if payment.booking and payment.booking.status == "completed":
        payment.booking.status = "paid"

    db.commit()
    db.refresh(payment)
    return payment


# ✅ 9️⃣ Delete payment (Admin only)
@router.delete("/{payment_id}", status_code=status.HTTP_200_OK)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("delete_payment")),
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}
