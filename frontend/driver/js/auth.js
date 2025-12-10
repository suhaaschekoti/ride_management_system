// driver/js/auth.js
import { apiFetch, parseJSON, setToken } from "./utils.js";

const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const errorEl = document.getElementById("error");
    errorEl.innerText = "";

    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    try {
      // 1️⃣ Attempt login
      const res = await apiFetch("/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });

      if (!res.ok) {
        const err = await parseJSON(res);
        errorEl.innerText = err?.detail || "Invalid credentials";
        return;
      }

      const data = await res.json();
      if (!data.access_token) throw new Error("No access token received");

      // 2️⃣ Save token
      setToken(data.access_token);

      // 3️⃣ Fetch user info
      const userRes = await apiFetch("/users/me");
      if (!userRes.ok) throw new Error("Failed to fetch user info");
      const user = await userRes.json();

      // 4️⃣ Fetch driver profile by user_id
      const driverRes = await apiFetch(`/drivers/by_user/${user.user_id}`);
      if (!driverRes.ok) throw new Error("Driver profile not found");
      const driver = await driverRes.json();

      if (!driver.driver_id) throw new Error("Driver ID missing in response");

      // 5️⃣ Save all driver details
      localStorage.setItem("driver_id", driver.driver_id);
      localStorage.setItem("email", user.email);
      localStorage.setItem("name", user.name);
      localStorage.setItem("user_id", user.user_id); // optional but useful

      console.log("✅ Logged in as driver:", driver.driver_id);

      // 6️⃣ Redirect to dashboard
      window.location.href = "dashboard.html";
    } catch (err) {
      console.error("Login error:", err);
      errorEl.innerText = err.message || "Login error";
    }
  });
}
