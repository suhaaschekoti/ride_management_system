// user/js/payments.js
import { apiFetch, parseJSON } from "./utils.js";

document.addEventListener("DOMContentLoaded", async () => {
  const pendingContainer = document.getElementById("pendingContainer");
  const completedContainer = document.getElementById("completedContainer");

  if (!pendingContainer || !completedContainer) return;

  // ⛑️ Added: detect if backend is reachable before loading
  const apiHealthy = await checkAPIHealth();
  if (!apiHealthy) {
    pendingContainer.innerHTML = `<p class="small" style="color:#b91c1c;">
      ❌ Cannot reach backend (check FastAPI server URL or CORS)
    </p>`;
    completedContainer.innerHTML = `<p class="small" style="color:#b91c1c;">
      ❌ Backend not reachable
    </p>`;
    return;
  }

  await loadPayments();

  async function loadPayments() {
    await Promise.all([loadPending(), loadCompleted()]);
  }

  // 🔹 Load Pending Payments
  async function loadPending() {
    pendingContainer.innerHTML = "<p>Loading pending payments...</p>";

    try {
      const res = await safeFetch("/payments/me/pending");
      if (!res.ok) {
        const err = await parseJSON(res);
        throw new Error(err?.detail || "Failed to load pending payments");
      }

      const payments = await res.json();
      if (!payments.length) {
        pendingContainer.innerHTML = `<p class="small" style="color:#555;">No pending payments 🎉</p>`;
        return;
      }

      pendingContainer.innerHTML = "";
      payments.forEach((p) => {
        const div = document.createElement("div");
        div.className = "card";
        div.style.margin = "8px 0";
        div.innerHTML = `
          <p><b>Booking ID:</b> ${p.booking_id}</p>
          <p><b>Transaction ID:</b> ${p.transaction_id}</p>
          <p><b>Amount:</b> ₹${p.amount.toFixed(2)}</p>
          <p><b>Status:</b> <span style="color:#b91c1c">${p.status}</span></p>

          <div class="form-row column" style="margin-top:8px;">
            <label class="small">Payment Method</label>
            <select id="method-${p.payment_id}" required>
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="upi">UPI</option>
            </select>
            <button class="btn pay-btn" data-id="${p.payment_id}" data-amount="${p.amount}">
              Complete Payment
            </button>
          </div>
        `;
        pendingContainer.appendChild(div);
      });

      document.querySelectorAll(".pay-btn").forEach((btn) =>
        btn.addEventListener("click", async (e) => {
          const id = e.target.dataset.id;
          const amount = parseFloat(e.target.dataset.amount);
          const method = document.getElementById(`method-${id}`).value;
          await completePayment(id, amount, method);
        })
      );
    } catch (err) {
      console.error("Error loading pending payments:", err);
      pendingContainer.innerHTML = `<p class="small" style="color:#b91c1c;">${err.message}</p>`;
    }
  }

  // 🔹 Load Completed Payments
  async function loadCompleted() {
    completedContainer.innerHTML = "<p>Loading completed payments...</p>";

    try {
      const res = await safeFetch("/payments/me/completed");
      if (!res.ok) {
        const err = await parseJSON(res);
        throw new Error(err?.detail || "Failed to load completed payments");
      }

      const payments = await res.json();
      if (!payments.length) {
        completedContainer.innerHTML = `<p class="small" style="color:#555;">No completed payments yet.</p>`;
        return;
      }

      completedContainer.innerHTML = "";
      payments.forEach((p) => {
        const div = document.createElement("div");
        div.className = "card";
        div.style.margin = "8px 0";
        div.innerHTML = `
          <p><b>Booking ID:</b> ${p.booking_id}</p>
          <p><b>Transaction ID:</b> ${p.transaction_id}</p>
          <p><b>Amount:</b> ₹${p.amount.toFixed(2)}</p>
          <p><b>Method:</b> ${p.payment_method}</p>
          <p><b>Status:</b> <span style="color:#16a34a">${p.status}</span></p>
          <p class="small" style="color:#666;">${new Date(p.timestamp).toLocaleString()}</p>
        `;
        completedContainer.appendChild(div);
      });
    } catch (err) {
      console.error("Error loading completed payments:", err);
      completedContainer.innerHTML = `<p class="small" style="color:#b91c1c;">${err.message}</p>`;
    }
  }

  // 🔹 Complete Payment
  async function completePayment(paymentId, amount, method) {
    if (!confirm("Confirm completing this payment?")) return;

    try {
      const res = await safeFetch(`/payments/${paymentId}/complete`, {
        method: "PUT",
        body: JSON.stringify({
          amount,
          payment_method: method,
        }),
      });

      if (!res.ok) {
        const err = await parseJSON(res);
        throw new Error(err?.detail || "Failed to complete payment");
      }

      alert("✅ Payment completed successfully!");
      loadPayments();
    } catch (err) {
      console.error("Payment completion error:", err);
      alert(err.message);
    }
  }

  // ✅ Safe fetch wrapper to catch "Failed to fetch" errors cleanly
  async function safeFetch(path, options = {}) {
    try {
      const res = await apiFetch(path, options);
      return res;
    } catch (err) {
      console.error("Network error:", err);
      throw new Error("Cannot reach API server. Make sure FastAPI is running and CORS allows this origin.");
    }
  }

  // ✅ Ping backend before loading payments
  async function checkAPIHealth() {
    try {
      const res = await fetch("http://127.0.0.1:8000/");
      return res.ok;
    } catch {
      return false;
    }
  }
});
