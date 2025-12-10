// driver/js/utils.js
const API_BASE = "http://127.0.0.1:8000"; // same backend base URL

export function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("driver_id");
  localStorage.removeItem("email");
  localStorage.removeItem("name");
}

// Wrapper for fetch that adds Authorization header and handles 401
export async function apiFetch(path, options = {}) {
  const url = API_BASE + path;
  const headers = options.headers || {};
  const token = getToken();

  if (token) headers["Authorization"] = `Bearer ${token}`;

  // Default content-type for JSON
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.href = "/driver/index.html"; // 🔄 redirect to driver login
    throw new Error("Unauthorized");
  }

  return res;
}

// Parse JSON safely
export async function parseJSON(res) {
  const txt = await res.text();
  if (!txt) return null;
  try {
    return JSON.parse(txt);
  } catch {
    return null;
  }
}
