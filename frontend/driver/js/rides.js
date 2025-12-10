// driver/js/rides.js
import { apiFetch, parseJSON, clearAuth } from './utils.js';

const ridesContainer = document.getElementById("ridesContainer");
const logoutBtn = document.getElementById("logoutBtn");

// ✅ Logout handler
if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    clearAuth();
    window.location.href = "index.html";
  });
}

// ✅ Fetch and display all rides for the logged-in driver
async function fetchRides() {
  try {
    // Step 1️⃣ - Get logged-in user
    const meRes = await apiFetch("/users/me");
    if (!meRes.ok) throw new Error("Unable to fetch user info");
    const me = await meRes.json();

    // Step 2️⃣ - Fetch corresponding driver profile
    const driverRes = await apiFetch(`/drivers/by_user/${me.user_id}`);
    if (!driverRes.ok) throw new Error("Driver profile not found");
    const driver = await driverRes.json();

    // Step 3️⃣ - Fetch all rides for this driver
    const ridesRes = await apiFetch(`/rides/driver/${driver.driver_id}`);
    if (!ridesRes.ok) throw new Error("Could not fetch rides");
    const rides = await ridesRes.json();

    renderRides(rides);
  } catch (err) {
    console.error("Error fetching rides:", err);
    ridesContainer.innerHTML = `<p style="color:red;">${err.message}</p>`;
  }
}

// ✅ Render rides into a dynamic, responsive table
function renderRides(rides) {
  if (!rides.length) {
    ridesContainer.innerHTML = `<p class="text-muted small">No rides found.</p>`;
    return;
  }

  const rows = rides.map((r) => {
    const booking = r.booking || {};
    const status = booking.status || r.status || "—";
    const hasFeedback = Boolean(r.driver_feedback || r.driver_rating);

    return `
      <tr>
        <td>${r.ride_id}</td>
        <td>${booking.pickup_location || r.pickup_location || "-"}</td>
        <td>${booking.dropoff_location || r.dropoff_location || "-"}</td>
        <td>${r.start_time ? new Date(r.start_time).toLocaleString() : "-"}</td>
        <td>${r.end_time ? new Date(r.end_time).toLocaleString() : "-"}</td>
        <td>₹${r.final_fare?.toFixed(2) || "—"}</td>
        <td><span class="status-tag status-${status.toLowerCase()}">${status}</span></td>
        <td>
          ${
            status === "completed"
              ? hasFeedback
                ? `<span class="text-muted small">Feedback Given</span>`
                : `
                  <div class="feedback-box">
                    <input type="number" class="rating-input" id="rating-${r.ride_id}" placeholder="⭐" min="1" max="5" />
                    <textarea id="feedback-${r.ride_id}" rows="2" placeholder="Leave feedback..."></textarea>
                    <button class="btn btn-sm btn-primary" onclick="submitFeedback(${r.ride_id})">Submit</button>
                  </div>
                `
              : `<span class="small text-muted">In progress</span>`
          }
        </td>
      </tr>
    `;
  }).join("");

  ridesContainer.innerHTML = `
    <div class="card shadow p-4">
      <h3 class="text-lg font-semibold mb-3">My Rides</h3>
      <div class="table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>ID</th>
              <th>Pickup</th>
              <th>Dropoff</th>
              <th>Start</th>
              <th>End</th>
              <th>Fare</th>
              <th>Status</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

// ✅ Submit feedback for a completed ride
window.submitFeedback = async function (rideId) {
  const rating = parseInt(document.getElementById(`rating-${rideId}`)?.value || 0);
  const feedback = document.getElementById(`feedback-${rideId}`)?.value.trim();

  if (!rating && !feedback) {
    alert("Please enter a rating or feedback before submitting.");
    return;
  }

  try {
    const res = await apiFetch(`/rides/${rideId}/feedback`, {
      method: "PUT",
      body: JSON.stringify({
        driver_rating: rating || null,
        driver_feedback: feedback || null,
      }),
    });

    if (!res.ok) {
      const err = await parseJSON(res);
      throw new Error(err?.detail || "Failed to submit feedback");
    }

    alert("✅ Feedback submitted successfully!");
    fetchRides(); // Refresh table after submission
  } catch (err) {
    console.error("Feedback error:", err);
    alert("❌ " + err.message);
  }
};

// ✅ Initialize on load
fetchRides();
