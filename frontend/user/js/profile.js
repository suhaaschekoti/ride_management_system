// user/js/profile.js
import { apiFetch, parseJSON } from './utils.js';

const form = document.getElementById("profileForm");
const msg = document.getElementById("msg");

async function loadProfile(){
  try{
    const res = await apiFetch("/users/me");
    if(!res.ok) throw new Error("Unauthorized");
    const me = await res.json();
    document.getElementById("name").value = me.name;
    document.getElementById("email").value = me.email;
    document.getElementById("phone").value = me.phone_number;
  } catch(err){
    window.location.href = "index.html";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  try{
    const resMe = await apiFetch("/users/me");
    const me = await resMe.json();
    const userId = me.user_id;

    const payload = {};
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const password = document.getElementById("password").value;

    if(name) payload.name = name;
    if(email) payload.email = email;
    if(phone) payload.phone_number = phone;
    if(password) payload.password = password;

    const res = await apiFetch(`/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });

    if(!res.ok){
      const err = await parseJSON(res);
      msg.innerText = err?.detail || "Update failed";
      msg.style.color = "#b91c1c";
      return;
    }
    const updated = await res.json();
    msg.innerText = "Profile updated";
    msg.style.color = "#064e3b";
  } catch(err){
    msg.innerText = err.message || "Error updating profile";
    msg.style.color = "#b91c1c";
  }
});

loadProfile();
