from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

app = FastAPI(title="Cab Booking API")




origins = [
    "http://127.0.0.1:5500",  # user site
    "http://127.0.0.1:5501",  # driver site
    "http://localhost:5500",
    "http://localhost:5501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5501"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import models

# Import all APIs
from apis import (
    user_api, role_api, permission_api,
    booking_api, ride_api, payment_api,
    driver_api, complaint_api, vehicle_api
)



# ✅ FIX 2: Include routers *after* CORS middleware registration
app.include_router(user_api.router)
app.include_router(role_api.router)
app.include_router(permission_api.router)
app.include_router(booking_api.router)
app.include_router(ride_api.router)
app.include_router(payment_api.router)
app.include_router(driver_api.router)
app.include_router(complaint_api.router)
app.include_router(vehicle_api.router)

# ✅ Initialize DB tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Cab Booking API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
