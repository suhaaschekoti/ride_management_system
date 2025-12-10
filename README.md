# ride_management_system

# Ride Booking & Management System

A full-stack ride-hailing platform built with FastAPI, SQLite, SQLAlchemy, Mapbox Directions API, and a simple HTML/CSS/JavaScript frontend.
Supports automatic driver assignment, fare calculation, mapping, payments, roles & permissions, and full ride lifecycle management.

## Features

### User Features
- Register, login, and update profile
- Book rides using map-based pickup and dropoff selection
- Automatic assignment of the nearest available driver
- View ride history
- File complaints
- Complete pending payments

### Driver Features
- Register as a driver
- Manage availability (online/offline)
- Update real-time location
- Automatically assigned to nearby bookings
- Start and end rides
- View earnings and recent activity dashboard
- View payments and vehicles

### Admin Features
- Full access via RBAC (Role-Based Access Control)
- Manage users, drivers, vehicles
- View all bookings, rides, complaints, and payments
- Assign permissions to roles
- Automatic admin creation and permissions seeding included

## Tech Stack

### Backend
| Component             | Technology                 |
|-----------------------|----------------------------|
| Framework             | FastAPI                    |
| Database              | SQLite with SQLAlchemy ORM |
| Models & Validation   | SQLAlchemy + Pydantic      |
| Authentication        | OAuth2 + JWT               |
| Authorization         | RBAC (Roles & Permissions) |
| Mapping               | Mapbox Directions API      |
| HTTP Client           | httpx (async)              |

### Frontend
- HTML  
- CSS  
- JavaScript  
- OpenStreetMap 

## Project Structure

```
project/
│
├── apis/
│   ├── user_apis.py
│   ├── driver_apis.py
│   ├── booking_apis.py
│   ├── ride_apis.py
│   ├── vehicle_apis.py
│   ├── payment_apis.py
│   ├── complaint_apis.py
│   ├── role_apis.py
│   └── permission_apis.py
│
├── frontend
├── models.py
├── schemas.py
├── database.py
├── utils.py
├── seed_permissions.py
├── create_admin.py
├── cab_booking.db
└── README.md
```

## Map Routing and Fare Calculation

### Mapbox Directions API
Used for:
- Retrieving driving distance  
- Calculating estimated travel duration  

### Fare Calculation Formula
```
fare = BASE_FARE + (PER_KM * distance_km) + (PER_MIN * duration_min)
minimum fare = 50
```

## Automatic Driver Assignment

1. The system retrieves all available drivers  
2. Assigns the nearest driver  
3. Marks driver as unavailable until ride completion  

On ride completion:
- Driver location updates to dropoff point  
- Driver becomes available again  

## Database Overview

Contains tables:
- Users
- Drivers
- Vehicles
- Bookings
- Rides
- Payments
- Complaints
- Roles
- Permissions
- RolePermissions

## Authentication and Authorization

JWT provides user authentication.  
RBAC ensures role-based access with permissions seeded automatically.

## Running the Project

### Install Dependencies
```
pip install -r requirements.txt
```

### Setup Database and Permissions
```
python seed_permissions.py
python create_admin.py
```

### Start API Server
```
uvicorn main:app --reload
```

### API Docs
```
http://127.0.0.1:8000/docs
```

## Future Enhancements
- Real-time GPS tracking
- WebSockets for ride updates
- Replace Euclidean with Haversine
- Enhanced frontend (React or SPA)
- Push notifications
