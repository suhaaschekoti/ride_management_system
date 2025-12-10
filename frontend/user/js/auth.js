// user/js/auth.js
import { apiFetch, parseJSON, setToken } from './utils.js';

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

if(loginForm){
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    // backend expects OAuth2 form-encoded; send as form data
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    try{
      const res = await apiFetch("/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString()
      });
      if(!res.ok){
        const err = await parseJSON(res);
        document.getElementById("error").innerText = err?.detail || "Login failed";
        return;
      }
      const data = await res.json();
      setToken(data.access_token);

      // fetch /users/me to obtain user_id and role info (for dashboard)
      const meRes = await apiFetch("/users/me");
      const me = await meRes.json();
      localStorage.setItem("user_id", me.user_id);
      // redirect to dashboard
      window.location.href = "dashboard.html";
    } catch(err){
      document.getElementById("error").innerText = err.message || "Login error";
    }
  });
}

if(registerForm){
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const password = document.getElementById("password").value;

    try{
      const res = await apiFetch("/users/users", {
        method: "POST",
        body: JSON.stringify({ name, email, phone_number: phone, password })
      });
      if(res.status === 201 || res.ok){
        alert("Account created. Please login.");
        window.location.href = "index.html";
        return;
      }
      const err = await parseJSON(res);
      document.getElementById("error").innerText = err?.detail || "Registration failed";
    } catch(err){
      document.getElementById("error").innerText = err.message || "Registration error";
    }
  });
}
