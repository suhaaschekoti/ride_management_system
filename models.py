from database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False)
    password = Column(String, nullable=False)
    rating = Column(Float, nullable=True, default=0)
    created_at = Column(Date, nullable=False)

    # Role-based access
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")
    bookings = relationship("Booking", back_populates="user")
    rides = relationship("Ride", back_populates="user")
    complaints = relationship("Complaint", back_populates="user")
    driver_profile = relationship("Driver", back_populates="user", uselist=False)  # ✅ link to Driver extension

    payments = relationship("Payment", back_populates="user", cascade="all, delete")



class Driver(Base):
    __tablename__ = "Drivers"

    driver_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    license = Column(String, nullable=False)
    experience_years = Column(Integer, nullable=True)
    

    # Relationships
    user = relationship("User", back_populates="driver_profile")  # ✅ extension link
    vehicles = relationship("Vehicle", back_populates="driver", cascade="all, delete")
    bookings = relationship("Booking", back_populates="driver", cascade="all, delete")
    rides = relationship("Ride", back_populates="driver", cascade="all, delete")





class Vehicle(Base):
    __tablename__ = "Vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("Drivers.driver_id", ondelete="CASCADE"), nullable=False)
    vehicle_type = Column(String, nullable=False)
    registration_number = Column(String, nullable=False, unique=True)
    model = Column(String, nullable=False)
    color = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    insurance_valid_till = Column(Date, nullable=False)

    driver = relationship("Driver", back_populates="vehicles")



class Booking(Base):
    __tablename__ = "Bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("Drivers.driver_id"))
    pickup_location = Column(String, nullable=False)
    dropoff_location = Column(String, nullable=False)
    pickup_time = Column(DateTime, nullable=False)
    dropoff_time = Column(DateTime, nullable=True)
    fare_estimate = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="bookings")
    driver = relationship("Driver", back_populates="bookings")

   
    payment = relationship("Payment", back_populates="booking", uselist=False)
    ride = relationship("Ride", back_populates="booking", uselist=False)






class Ride(Base):
    __tablename__ = "Rides"

    ride_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Bookings.booking_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("Drivers.driver_id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    distance_travelled = Column(Float, nullable=False)
    final_fare = Column(Float, nullable=False)
    rating_by_user = Column(Integer, nullable=True)
    rating_by_driver = Column(Integer, nullable=True)
    feedback = Column(String, nullable=True)

    
    booking = relationship("Booking", back_populates="ride")
    user = relationship("User", back_populates="rides")
    driver = relationship("Driver", back_populates="rides")
    complaints = relationship("Complaint", back_populates="ride")



class Payment(Base):
    __tablename__ = "Payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Bookings.booking_id"), unique=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)  # ✅ add this
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    transaction_id = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    booking = relationship("Booking", back_populates="payment")
    user = relationship("User", back_populates="payments")






class Complaint(Base):
    __tablename__ = "Complaints"

    complaint_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    ride_id = Column(Integer, ForeignKey("Rides.ride_id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)  
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

   
    user = relationship("User", back_populates="complaints")
    ride = relationship("Ride", back_populates="complaints")

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")  # from User model
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete")

    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name})>"


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    def __repr__(self):
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"
