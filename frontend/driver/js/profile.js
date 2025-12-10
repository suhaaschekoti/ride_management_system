import { apiFetch, clearAuth } from './utils.js';

const form = document.getElementById('profileForm');
const msgEl = document.getElementById('msg');
const logoutBtn = document.getElementById('logoutBtn');
const vehicleContainer = document.getElementById('vehicleContainer');

let currentDriver = null;

// ✅ Logout
logoutBtn?.addEventListener('click', () => {
  clearAuth();
  window.location.href = 'index.html';
});

// ✅ Load Profile
async function loadProfile() {
  try {
    const meRes = await apiFetch('/users/me');
    if (!meRes.ok) throw new Error('Unable to fetch user info');
    const me = await meRes.json();

    const driverRes = await apiFetch(`/drivers/by_user/${me.user_id}`);
    if (!driverRes.ok) throw new Error('Driver profile not found');
    const driver = await driverRes.json();
    currentDriver = driver;

    document.getElementById('name').value = driver.user.name;
    document.getElementById('email').value = driver.user.email;
    document.getElementById('phone').value = driver.user.phone_number;
    document.getElementById('license').value = driver.license;
    document.getElementById('experience').value = driver.experience_years ?? 0;

    await loadVehicle(driver.driver_id);
  } catch (err) {
    msgEl.textContent = err.message;
    msgEl.classList.remove('success');
    msgEl.classList.add('error');
  }
}

// ✅ Load Vehicle(s)
async function loadVehicle(driverId) {
  try {
    const res = await apiFetch(`/vehicles/driver/${driverId}`);
    if (!res.ok) {
      vehicleContainer.innerHTML = `
        <div class="vehicle-details" style="text-align:center; color:#6b7280;">
          <p><em>No vehicle assigned yet.</em></p>
        </div>`;
      return;
    }

    const vehicles = await res.json();

    if (!vehicles.length) {
      vehicleContainer.innerHTML = `
        <div class="vehicle-details" style="text-align:center; color:#6b7280;">
          <p><em>No vehicle assigned yet.</em></p>
        </div>`;
      return;
    }

    // Display all vehicles if there are multiple
    vehicleContainer.innerHTML = vehicles
      .map(
        (v) => `
        <div class="vehicle-details">
          <p><span>Model:</span> ${v.model || '-'}</p>
          <p><span>Type:</span> ${v.vehicle_type || '-'}</p>
          <p><span>Registration #:</span> ${v.registration_number || '-'}</p>
          <p><span>Color:</span> ${v.color || '-'}</p>
          <p><span>Capacity:</span> ${v.capacity ?? '-'}</p>
          <p><span>Insurance Valid Till:</span> ${
            v.insurance_valid_till
              ? new Date(v.insurance_valid_till).toLocaleDateString()
              : '-'
          }</p>
        </div>`
      )
      .join('');
  } catch (err) {
    console.error(err);
    vehicleContainer.innerHTML =
      '<p style="color:red;">Error loading vehicle info.</p>';
  }
}

// ✅ Save Profile Updates
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  msgEl.textContent = '';
  msgEl.classList.remove('success', 'error');

  try {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const license = document.getElementById('license').value.trim();
    const experience =
      parseInt(document.getElementById('experience').value.trim()) || 0;
    const password = document.getElementById('password').value.trim();

    const meRes = await apiFetch('/users/me');
    const me = await meRes.json();

    const userPayload = { name, email, phone_number: phone };
    if (password) userPayload.password = password;

    const userUpdate = await apiFetch(`/users/${me.user_id}`, {
      method: 'PUT',
      body: JSON.stringify(userPayload),
    });
    if (!userUpdate.ok) throw new Error('Failed to update user details');

    const driverPayload = { license, experience_years: experience };
    const driverUpdate = await apiFetch(`/drivers/${currentDriver.driver_id}`, {
      method: 'PUT',
      body: JSON.stringify(driverPayload),
    });
    if (!driverUpdate.ok) throw new Error('Failed to update driver profile');

    msgEl.textContent = 'Profile updated successfully!';
    msgEl.classList.add('success');
    document.getElementById('password').value = '';
  } catch (err) {
    msgEl.textContent = err.message;
    msgEl.classList.add('error');
  }
});

// ✅ Initialize
loadProfile();
