// user/js/rides.js
import { apiFetch, parseJSON } from './utils.js';

async function loadRides() {
  try {
    const meRes = await apiFetch("/users/me");
    if (!meRes.ok) throw new Error("Not logged in");
    const me = await meRes.json();

    const res = await apiFetch(`/rides/user/${me.user_id}`);
    if (!res.ok) {
      const err = await parseJSON(res);
      document.getElementById("ridesArea").innerText =
        err?.detail || "Failed to load rides";
      return;
    }

    const rides = await res.json();
    if (!rides.length) {
      document.getElementById("ridesArea").innerHTML =
        "<p class='small'>No rides yet</p>";
      return;
    }

    const table = document.createElement("table");
    table.className = "table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>ID</th>
          <th>From</th>
          <th>To</th>
          <th>Status</th>
          <th>Fare</th>
          <th>Rating</th>
          <th>Actions</th>
        </tr>
      </thead>
    `;

    const tbody = document.createElement("tbody");
    rides.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.ride_id}</td>
        <td>${r.start_time ? new Date(r.start_time).toLocaleString() : "-"}</td>
        <td>${r.end_time ? new Date(r.end_time).toLocaleString() : "-"}</td>
        <td>${r.booking?.status ?? "—"}</td>
        <td>${r.final_fare ?? "-"}</td>
        <td>${r.rating_by_user ?? "-"}</td>
        <td><button class="btn" data-ride="${r.ride_id}">Leave Feedback</button></td>
      `;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    const ridesArea = document.getElementById("ridesArea");
    ridesArea.innerHTML = "";
    ridesArea.appendChild(table);

    // Attach feedback handlers
    document.querySelectorAll("button[data-ride]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const rideId = e.target.dataset.ride;
        const rating = prompt("Rate driver (1-5):");
        if (!rating) return;
        const feedback = prompt("Optional feedback:");

        const res = await apiFetch(`/rides/${rideId}/feedback`, {
          method: "PUT",
          body: JSON.stringify({
            user_rating: parseInt(rating),
            user_feedback: feedback,
          }),
        });

        if (!res.ok) {
          alert("Failed to submit feedback");
        } else {
          alert("Thanks for your feedback!");
          loadRides();
        }
      });
    });
  } catch (err) {
    console.error("Error loading rides:", err);
    window.location.href = "index.html";
  }
}

loadRides();
