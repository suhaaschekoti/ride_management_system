// user/js/booking.js
import { apiFetch, parseJSON } from './utils.js';

const form = document.getElementById("bookForm");
const msg = document.getElementById("message");

if(!form) throw new Error("bookForm not found");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  try{
    // ensure logged in
    const meRes = await apiFetch("/users/me");
    if(!meRes.ok) throw new Error("Not logged in");
    const me = await meRes.json();
    const user_id = me.user_id;

    const pickup = document.getElementById("pickup").value.trim();
    const dropoff = document.getElementById("dropoff").value.trim();
    const pickup_time = document.getElementById("pickup_time").value;
    const fare_estimate = parseFloat(document.getElementById("fare_estimate").value || 0);

    const payload = {
      user_id,
      pickup_location: pickup,
      dropoff_location: dropoff,
      pickup_time: new Date(pickup_time).toISOString(),
      fare_estimate
    };

    const res = await apiFetch("/bookings/", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    if(!res.ok){
      const err = await parseJSON(res);
      msg.innerText = err?.detail || "Booking failed";
      msg.style.color = "#b91c1c";
      return;
    }

    const booking = await res.json();
    msg.innerHTML = `Booking requested. <a href="booking_status.html?booking_id=${booking.booking_id}">View status</a>`;
    msg.style.color = "#064e3b";
  } catch(err){
    msg.innerText = err.message || "Error creating booking";
    msg.style.color = "#b91c1c";
  }
});
