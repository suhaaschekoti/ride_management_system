import { apiFetch } from "./utils.js";

document.addEventListener("DOMContentLoaded", async () => {
  const bookingsDiv =
    document.getElementById("bookingsList") ||
    document.getElementById("bookingsContainer");
  if (!bookingsDiv) return;

  bookingsDiv.innerHTML = "<p>Loading your bookings...</p>";

  try {
    // ✅ Step 1: Get the current logged-in user from token
    const meRes = await apiFetch("/users/me");
    if (!meRes.ok) throw new Error("Session expired. Please log in again.");
    const me = await meRes.json();
    console.log("👤 Logged-in user:", me);

    // ✅ Step 2: Fetch bookings for that user
    const res = await apiFetch(`/bookings/user/me`);
    if (!res.ok)
      throw new Error(`Failed to load bookings (${res.status})`);
    const bookings = await res.json();

    // ✅ Step 3: Display the bookings
    if (!bookings.length) {
      bookingsDiv.innerHTML = "<p>No bookings yet.</p>";
      return;
    }

    bookingsDiv.innerHTML = bookings
      .map(
        (b) => `
        <div class="booking-card">
          <p><b>ID:</b> ${b.booking_id}</p>
          <p><b>Pickup:</b> ${b.pickup_location}</p>
          <p><b>Dropoff:</b> ${b.dropoff_location}</p>
          <p><b>Status:</b> <span class="status ${b.status}">${b.status}</span></p>
          <p><b>Fare Estimate:</b> ₹${b.fare_estimate}</p>
          ${
            b.status === "pending_user_confirmation"
              ? `<button class="btn confirm-btn" data-id="${b.booking_id}">Confirm Booking</button>`
              : ""
          }
        </div>`
      )
      .join("");

    // ✅ Step 4: Add confirmation handlers
    document.querySelectorAll(".confirm-btn").forEach((btn) =>
      btn.addEventListener("click", async (e) => {
        const bookingId = e.target.dataset.id;
        try {
          const confirmRes = await apiFetch(`/bookings/${bookingId}/confirm`, {
            method: "PUT",
          });
          if (!confirmRes.ok) throw new Error("Confirmation failed");
          alert("Booking confirmed!");
          window.location.reload();
        } catch (err) {
          alert(err.message);
        }
      })
    );
  } catch (err) {
    console.error("Error fetching bookings:", err);
    bookingsDiv.innerHTML = `<p class="error">${err.message}</p>`;
  }
});
