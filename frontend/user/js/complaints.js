import { apiFetch, parseJSON, clearAuth } from './utils.js';

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearAuth();
  window.location.href = "index.html";
});

async function loadComplaints() {
  const container = document.getElementById("complaintsArea");
  container.innerHTML = "<p>Loading...</p>";

  try {
    const meRes = await apiFetch("/users/me");
    if (!meRes.ok) throw new Error("Not logged in");
    const me = await meRes.json();

    const res = await apiFetch(`/complaints/user/${me.user_id}`);
    if (!res.ok) {
      const err = await parseJSON(res);
      container.innerHTML = `<p class="error">${err?.detail || "Failed to load complaints"}</p>`;
      return;
    }

    const complaints = await res.json();
    if (!complaints.length) {
      container.innerHTML = `<p class="small">No complaints filed yet.</p>`;
      return;
    }

    const table = document.createElement("table");
    table.className = "table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>ID</th>
          <th>Ride ID</th>
          <th>Description</th>
          <th>Status</th>
          <th>Filed At</th>
          <th>Resolved At</th>
          <th>Actions</th>
        </tr>
      </thead>
    `;

    const tbody = document.createElement("tbody");
    complaints.forEach(c => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${c.complaint_id}</td>
        <td>${c.ride_id}</td>
        <td>${c.description}</td>
        <td>${c.status}</td>
        <td>${new Date(c.created_at).toLocaleString()}</td>
        <td>${c.resolved_at ? new Date(c.resolved_at).toLocaleString() : "—"}</td>
        <td>
          <button class="btn small danger" data-id="${c.complaint_id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.innerHTML = "";
    container.appendChild(table);

    // delete handlers
    document.querySelectorAll('button[data-id]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.target.dataset.id;
        if (!confirm("Delete this complaint?")) return;
        const res = await apiFetch(`/complaints/${id}`, { method: "DELETE" });
        if (!res.ok) {
          alert("Failed to delete complaint");
        } else {
          alert("Complaint deleted");
          loadComplaints();
        }
      });
    });

  } catch (err) {
    console.error(err);
    window.location.href = "index.html";
  }
}

// ✅ Handle complaint submission
document.getElementById("complaintForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const rideId = document.getElementById("rideId").value.trim();
  const description = document.getElementById("complaintDesc").value.trim();

  if (!rideId || !description) {
    alert("Please fill all fields");
    return;
  }

  try {
    const meRes = await apiFetch("/users/me");
    const me = await meRes.json();

    const body = {
      user_id: me.user_id,
      ride_id: parseInt(rideId),
      description: description,
    };

    const res = await apiFetch("/complaints", {
      method: "POST",
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await parseJSON(res);
      alert(err?.detail || "Failed to submit complaint");
      return;
    }

    alert("Complaint submitted successfully!");
    document.getElementById("complaintForm").reset();
    loadComplaints();
  } catch (err) {
    console.error(err);
    alert("Something went wrong.");
  }
});

loadComplaints();
