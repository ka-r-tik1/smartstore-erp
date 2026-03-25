// SmartStore ERP — Config + API Helper
// API base URL aur token management

const API_BASE = "https://overmerciful-genesis-barbellate.ngrok-free.dev";  // ngrok URL

let authToken = localStorage.getItem("smartstore_token") || null;
let currentUser = JSON.parse(localStorage.getItem("smartstore_user") || "null");

// API call helper — har request mein token auto-attach hoga
async function apiCall(endpoint, method = "GET", body = null) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
      ...(authToken ? { "Authorization": "Bearer " + authToken } : {})
    }
  };
  if (body) opts.body = JSON.stringify(body);

  const response = await fetch(API_BASE + endpoint, opts);
  const data = await response.json();

  if (!response.ok) {
    const msg = data.detail || "API error";
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

// Token save/clear
function saveAuth(token, user) {
  authToken = token;
  currentUser = user;
  localStorage.setItem("smartstore_token", token);
  localStorage.setItem("smartstore_user", JSON.stringify(user));
}

function clearAuth() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem("smartstore_token");
  localStorage.removeItem("smartstore_user");
}

function isLoggedIn() {
  return !!authToken;
}
