// user/js/dashboard.js
import { apiFetch, parseJSON, clearAuth } from './utils.js';

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearAuth();
  window.location.href = "index.html";
});

async function loadDashboard(){
  try {
    const meRes = await apiFetch("/users/me");
    if (!meRes.ok) throw new Error("Not authorized");
    const me = await meRes.json();

    document.getElementById("welcome").innerHTML = `
      <strong>Hello, ${me.name}</strong>
      <div class="small">Member since ${me.created_at}</div>
    `;

    // Fetch recent rides (limit to 5)
    const ridesRes = await apiFetch(`/rides/user/${me.user_id}`);
    if (!ridesRes.ok) {
      const err = await parseJSON(ridesRes);
      document.getElementById("recentRides").innerHTML = `<p>${err?.detail || "Failed to load rides"}</p>`;
      return;
    }

    const rides = await ridesRes.json();
    const recent = rides.slice(0, 5);
    const container = document.getElementById("recentRides");

    if (!recent.length) {
      container.innerHTML = `<p class="small">No rides yet</p>`;
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
        </tr>
      </thead>
    `;

    const tbody = document.createElement("tbody");

    recent.forEach(r => {
      const status = r.booking?.status?.toLowerCase() || 'unknown';
      let statusBadge = '';

      switch (status) {
        case 'completed':
          statusBadge = `<span class="badge bg-success">Completed</span>`;
          break;
        case 'ongoing':
          statusBadge = `<span class="badge bg-warning text-dark">Ongoing</span>`;
          break;
        case 'cancelled':
          statusBadge = `<span class="badge bg-danger">Cancelled</span>`;
          break;
        default:
          statusBadge = `<span class="badge bg-secondary">${status}</span>`;
          break;
      }

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.ride_id || '-'}</td>
        <td>${r.start_time ? new Date(r.start_time).toLocaleString() : r.pickup_location || '-'}</td>
        <td>${r.end_time ? new Date(r.end_time).toLocaleString() : r.dropoff_location || '-'}</td>
        <td class="small">${statusBadge}</td>
      `;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.innerHTML = "";
    container.appendChild(table);

  } catch (err) {
    console.error("Dashboard load failed:", err);
    window.location.href = "index.html";
  }
}

loadDashboard();
