// driver/js/dashboard.js
import { apiFetch, parseJSON, clearAuth, getToken } from "./utils.js";

// 🚪 Logout button
document.getElementById("logoutBtn").addEventListener("click", () => {
  clearAuth();
  window.location.href = "index.html";
});

async function loadDriverDashboard() {
  try {
    const token = getToken();
    if (!token) {
      console.warn("No token found, redirecting to login...");
      clearAuth();
      window.location.href = "index.html";
      return;
    }

    // Get driver_id from localStorage
    const driverId = localStorage.getItem("driver_id");
    if (!driverId) {
      throw new Error("Driver ID not found in localStorage");
    }

    // 1️⃣ Get current user
    const userRes = await apiFetch("/users/me");
    if (!userRes.ok) throw new Error("Not authorized");
    const user = await userRes.json();

    document.getElementById("welcome").innerHTML = `
      <strong>Hello, ${user.name}</strong>
      <div class="small">${user.email}</div>
    `;

    // 2️⃣ Fetch driver dashboard using driver_id
    const dashRes = await apiFetch(`/drivers/${driverId}/dashboard`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!dashRes.ok) {
      const err = await parseJSON(dashRes);
      console.error("Dashboard error response:", err);
      throw new Error(err?.detail || "Failed to load dashboard");
    }

    const dashboard = await dashRes.json();

    // 3️⃣ Fill summary cards
    document.getElementById("totalRides").textContent = dashboard.total_rides || 0;
    document.getElementById("completedRides").textContent = dashboard.completed_rides || 0;
    document.getElementById("totalEarnings").textContent = `₹${(dashboard.total_earnings || 0).toFixed(2)}`;
    document.getElementById("rating").textContent = `⭐ ${(dashboard.avg_rating || 0).toFixed(1)}`;

    // 4️⃣ Show recent rides
    const container = document.getElementById("recentRides");
    const rides = dashboard.recent_rides || [];

    if (!rides.length) {
      container.innerHTML = `<p class="small text-muted">No recent rides yet</p>`;
      return;
    }

    const table = document.createElement("table");
    table.className = "table align-middle table-striped";
    table.innerHTML = `
      <thead>
        <tr>
          <th>ID</th>
          <th>Pickup</th>
          <th>Dropoff</th>
          <th>Status</th>
        </tr>
      </thead>
    `;

    const tbody = document.createElement("tbody");
    rides.forEach((r) => {
      const status = (r.status || "unknown").toLowerCase();
      let badge = "";

      switch (status) {
        case "completed":
          badge = `<span class="badge bg-success">Completed</span>`;
          break;
        case "ongoing":
          badge = `<span class="badge bg-warning text-dark">Ongoing</span>`;
          break;
        case "cancelled":
          badge = `<span class="badge bg-danger">Cancelled</span>`;
          break;
        default:
          badge = `<span class="badge bg-secondary">${status}</span>`;
      }

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.ride_id}</td>
        <td>${r.pickup || "-"}</td>
        <td>${r.dropoff || "-"}</td>
        <td>${badge}</td>
      `;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.innerHTML = "";
    container.appendChild(table);
  } catch (err) {
    console.error("Driver dashboard load failed:", err);
    document.getElementById("welcome").innerHTML = `
      <div class="text-danger">⚠️ Error loading dashboard</div>
    `;
  }
}

// 🚀 Run on page load
loadDriverDashboard();
