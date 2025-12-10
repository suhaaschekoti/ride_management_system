// driver/js/complaints.js
import { apiFetch, parseJSON, clearAuth } from './utils.js';

const form = document.getElementById("complaintForm");
const container = document.getElementById("complaintsContainer");
const msg = document.getElementById("formMessage");
const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    clearAuth();
    window.location.href = "index.html";
  });
}

async function fetchComplaints() {
  try {
    const meRes = await apiFetch("/users/me");
    const me = await meRes.json();

    const res = await apiFetch(`/complaints/user/${me.user_id}`);
    if (!res.ok) throw new Error("Failed to load complaints");
    const complaints = await res.json();

    renderComplaints(complaints);
  } catch (err) {
    container.innerHTML = `<p style="color:red;">${err.message}</p>`;
  }
}

function renderComplaints(list) {
  if (!list.length) {
    container.innerHTML = "<p>No complaints filed yet.</p>";
    return;
  }

  const rows = list.map(c => `
    <tr>
      <td>${c.complaint_id}</td>
      <td>${c.ride_id}</td>
      <td>${c.description}</td>
      <td><span class="status-tag status-${c.status}">${c.status}</span></td>
      <td>${new Date(c.created_at).toLocaleString()}</td>
      <td>${c.resolved_at ? new Date(c.resolved_at).toLocaleString() : '-'}</td>
      <td>
        ${c.status === "open" ? 
          `<button class="delete-btn" onclick="deleteComplaint(${c.complaint_id})">Delete</button>` 
          : "-"}
      </td>
    </tr>
  `).join("");

  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Ride ID</th>
          <th>Description</th>
          <th>Status</th>
          <th>Created</th>
          <th>Resolved</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// Handle new complaint submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  msg.textContent = "";

  const rideId = document.getElementById("rideId").value.trim();
  const desc = document.getElementById("description").value.trim();
  if (!rideId || !desc) return (msg.textContent = "All fields required.");

  try {
    const meRes = await apiFetch("/users/me");
    const me = await meRes.json();

    const res = await apiFetch("/complaints", {
      method: "POST",
      body: JSON.stringify({
        user_id: me.user_id,
        ride_id: parseInt(rideId),
        description: desc
      }),
    });

    if (!res.ok) {
      const err = await parseJSON(res);
      throw new Error(err?.detail || "Failed to file complaint");
    }

    alert("Complaint submitted successfully.");
    form.reset();
    fetchComplaints();
  } catch (err) {
    msg.textContent = err.message;
  }
});

// Delete complaint
window.deleteComplaint = async function (id) {
  if (!confirm("Delete this complaint?")) return;
  try {
    const res = await apiFetch(`/complaints/${id}`, { method: "DELETE" });
    if (res.status !== 204) throw new Error("Could not delete complaint");
    fetchComplaints();
  } catch (err) {
    alert(err.message);
  }
};

// Init
fetchComplaints();
