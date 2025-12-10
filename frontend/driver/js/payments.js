// driver/js/payments.js
import { apiFetch, parseJSON, clearAuth } from './utils.js';

const logoutBtn = document.getElementById("logoutBtn");
const container = document.getElementById("paymentsContainer");
const totalEarningsEl = document.getElementById("totalEarnings");
const completedCountEl = document.getElementById("completedCount");
const pendingCountEl = document.getElementById("pendingCount");

// ✅ Logout functionality
if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    clearAuth();
    window.location.href = "index.html";
  });
}

// ✅ Fetch driver payments directly (backend identifies driver from token)
async function fetchPayments() {
  try {
    const payRes = await apiFetch(`/payments/driver-payments`);
    if (!payRes.ok) {
      const err = await parseJSON(payRes);
      throw new Error(err?.detail || "Unable to load payments");
    }

    const payments = await payRes.json();
    renderPayments(payments);
    calculateSummary(payments);

  } catch (err) {
    console.error("Error loading payments:", err);
    container.innerHTML = `<p style="color:red;">${err.message}</p>`;
  }
}

// ✅ Render payments table
function renderPayments(payments) {
  if (!payments.length) {
    container.innerHTML = "<p>No payments found yet.</p>";
    return;
  }

  const rows = payments
    .map(
      (p) => `
      <tr>
        <td>${p.payment_id}</td>
        <td>${p.ride_id || '-'}</td>
        <td>₹${p.amount?.toFixed(2) || '0.00'}</td>
        <td>${p.payment_method || '-'}</td>
        <td><span class="status-tag status-${p.status}">${p.status}</span></td>
        <td>${p.timestamp ? new Date(p.timestamp).toLocaleString() : '-'}</td>
      </tr>
    `
    )
    .join("");

  container.innerHTML = `
    <table class="table table-striped align-middle">
      <thead>
        <tr>
          <th>ID</th>
          <th>Ride ID</th>
          <th>Amount</th>
          <th>Method</th>
          <th>Status</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ✅ Calculate totals
function calculateSummary(payments) {
  let total = 0;
  let completed = 0;
  let pending = 0;

  payments.forEach((p) => {
    if (p.status === "completed") {
      total += p.amount || 0;
      completed++;
    } else if (p.status === "pending") {
      pending++;
    }
  });

  totalEarningsEl.textContent = `₹${total.toFixed(2)}`;
  completedCountEl.textContent = completed;
  pendingCountEl.textContent = pending;
}

// 🚀 Init
fetchPayments();
