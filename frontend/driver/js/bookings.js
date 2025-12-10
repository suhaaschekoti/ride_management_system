// ===================== CONFIG =====================
const API_BASE_URL = "http://127.0.0.1:8000"; // ✅ Base API URL
const token = localStorage.getItem("access_token");
const driverId = localStorage.getItem("driver_id");

// ===================== AUTH CHECK =====================
if (!token || !driverId) {
  alert("Session expired. Please log in again.");
  window.location.href = "index.html"; // ✅ Redirect to driver login
}

const headers = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${token}`,
};

// ===================== LOAD AVAILABLE BOOKINGS =====================
async function loadAvailableBookings() {
  const tableBody = document.querySelector("#available-bookings-table tbody");
  const errorText = document.getElementById("available-bookings-error");
  tableBody.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";
  errorText.textContent = "";

  try {
    const res = await fetch(`${API_BASE_URL}/bookings/available`, {
      headers,
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to load available bookings: ${res.status} ${errText}`);
    }

    const data = await res.json();

    if (!data.length) {
      tableBody.innerHTML = "<tr><td colspan='6'>No available bookings.</td></tr>";
      return;
    }

    tableBody.innerHTML = data
      .map(
        (b) => `
          <tr>
            <td>${b.booking_id}</td>
            <td>${b.pickup_location}</td>
            <td>${b.dropoff_location}</td>
            <td>${new Date(b.pickup_time).toLocaleString()}</td>
            <td>₹${b.fare_estimate?.toFixed(2) || "N/A"}</td>
            <td>
              <button class="action-btn" onclick="acceptBooking(${b.booking_id})">Accept</button>
            </td>
          </tr>`
      )
      .join("");
  } catch (err) {
    console.error("Error loading available bookings:", err);
    errorText.textContent = err.message;
  }
}

// ===================== FETCH DRIVER’S OWN BOOKINGS =====================
async function fetchMyBookings() {
  const tableBody = document.querySelector("#my-bookings-table tbody");
  const errorText = document.getElementById("my-bookings-error");
  tableBody.innerHTML = "<tr><td colspan='7'>Loading...</td></tr>";
  errorText.textContent = "";

  try {
    const res = await fetch(`${API_BASE_URL}/bookings/driver/${driverId}`, { headers });
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();

    if (!data.length) {
      tableBody.innerHTML = "<tr><td colspan='7'>No bookings found.</td></tr>";
      return;
    }

    tableBody.innerHTML = data
      .map((b) => {
        const actionBtn =
          b.status === "accepted"
            ? `<button class="action-btn" onclick="startRide(${b.booking_id})">Start</button>`
            : b.status === "ongoing"
            ? `<button class="action-btn" onclick="endRide(${b.booking_id})">End</button>`
            : "—";

        return `
          <tr>
            <td>${b.booking_id}</td>
            <td>${b.pickup_location}</td>
            <td>${b.dropoff_location}</td>
            <td>${b.status}</td>
            <td>${new Date(b.pickup_time).toLocaleString()}</td>
            <td>${b.fare_estimate ? `₹${b.fare_estimate.toFixed(2)}` : "N/A"}</td>
            <td>${actionBtn}</td>
          </tr>`;
      })
      .join("");
  } catch (err) {
    console.error("Error fetching driver bookings:", err);
    errorText.textContent = "Failed to load your bookings.";
  }
}

// ===================== ACCEPT BOOKING =====================
async function acceptBooking(bookingId) {
  const proposedFare = prompt("Enter your proposed fare:");
  if (!proposedFare || isNaN(proposedFare)) {
    alert("Invalid fare amount.");
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE_URL}/bookings/${bookingId}/accept?proposed_fare=${encodeURIComponent(proposedFare)}`,
      {
        method: "PUT",
        headers,
      }
    );
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Error ${res.status}: ${errText}`);
    }
    alert("Booking accepted successfully!");
    await loadAvailableBookings();
    await fetchMyBookings();
  } catch (err) {
    console.error("Error accepting booking:", err);
    alert("Failed to accept booking: " + err.message);
  }
}

// ===================== START RIDE =====================
async function startRide(bookingId) {
  if (!confirm("Start this ride?")) return;
  try {
    const res = await fetch(`${API_BASE_URL}/bookings/${bookingId}/start`, {
      method: "PUT",
      headers,
    });
    if (!res.ok) throw new Error(`Error ${res.status}`);
    alert("Ride started!");
    await fetchMyBookings();
  } catch (err) {
    console.error("Error starting ride:", err);
    alert("Failed to start ride.");
  }
}

// ===================== END RIDE =====================
async function endRide(bookingId) {
  if (!confirm("End this ride?")) return;
  try {
    const res = await fetch(`${API_BASE_URL}/bookings/${bookingId}/end`, {
      method: "PUT",
      headers,
    });
    if (!res.ok) throw new Error(`Error ${res.status}`);
    alert("Ride ended successfully!");
    await fetchMyBookings();
  } catch (err) {
    console.error("Error ending ride:", err);
    alert("Failed to end ride.");
  }
}

// ===================== LOGOUT HANDLER =====================
document.getElementById("logout-btn").addEventListener("click", () => {
  localStorage.clear();
  window.location.href = "index.html";
});

// ===================== INITIALIZE =====================
loadAvailableBookings();
fetchMyBookings();
