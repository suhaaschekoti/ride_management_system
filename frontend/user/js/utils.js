// user/js/utils.js
const API_BASE = "http://127.0.0.1:8000"; // change if needed

export function getToken(){
  return localStorage.getItem("access_token"); // ✅ unified name
}

export function setToken(token){
  localStorage.setItem("access_token", token); // ✅ unified name
}

export function clearAuth(){
  localStorage.removeItem("access_token"); // ✅ unified name
  localStorage.removeItem("user_id");
  localStorage.removeItem("role");
}

// Wrapper for fetch that adds Authorization header and handles 401
export async function apiFetch(path, options = {}){
  const url = API_BASE + path;
  const headers = options.headers || {};
  const token = getToken();

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Default content-type for JSON if body provided
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    // Invalid token — clear and redirect to login
    clearAuth();
    window.location.href = "/user/index.html";
    throw new Error("Unauthorized");
  }

  return res;
}

// Convenience: parse JSON but handle empty responses
export async function parseJSON(res){
  const txt = await res.text();
  if (!txt) return null;
  try { return JSON.parse(txt); } catch(e) { return null; }
}
