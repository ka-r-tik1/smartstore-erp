// SmartStore ERP — Auth (Login/Logout) with Envelope Animation

let opened = false;

document.addEventListener("DOMContentLoaded", function() {
  checkAuthState();
});

function checkAuthState() {
  const loginWrap = document.getElementById("login-wrap");
  const appShell = document.querySelector(".app-shell");

  if (isLoggedIn()) {
    loginWrap.style.display = "none";
    appShell.style.display = "";
    updateUserDisplay();
    // Auto-load dashboard data
    if (typeof loadDashboard === 'function') {
      setTimeout(loadDashboard, 100);
    }
  } else {
    loginWrap.style.display = "block";
    appShell.style.display = "none";
    // Reset envelope state
    closeEnv();
  }
}

function updateUserDisplay() {
  const el = document.getElementById("user-display-name");
  if (el && currentUser) {
    el.textContent = currentUser.full_name || currentUser.username;
  }
  const roleEl = document.getElementById("user-display-role");
  if (roleEl && currentUser) {
    roleEl.textContent = currentUser.role.toUpperCase();
  }
}

function openEnv() {
  if (opened) return;
  opened = true;
  document.getElementById('env').classList.add('open');
  document.getElementById('hint').classList.add('hidden');
  document.getElementById('env').style.cursor = 'default';
}

function closeEnv() {
  opened = false;
  const env = document.getElementById('env');
  if (!env) return;
  env.classList.remove('open');
  env.style.cursor = 'pointer';
  const hint = document.getElementById('hint');
  if (hint) hint.classList.remove('hidden');
  // reset form
  const uname = document.getElementById('uname');
  const pass = document.getElementById('pass');
  const err = document.getElementById('err');
  const btn = document.getElementById('btn');
  if (uname) uname.value = '';
  if (pass) pass.value = '';
  if (err) err.style.display = 'none';
  if (btn) {
    btn.textContent = 'Sign In';
    btn.style.pointerEvents = 'all';
    btn.style.opacity = '1';
  }
}

// Click outside envelope closes it
document.addEventListener('click', function(e) {
  if (!opened) return;
  const env = document.getElementById('env');
  if (env && !env.contains(e.target)) {
    closeEnv();
  }
});

async function doLogin() {
  const u = document.getElementById('uname').value.trim();
  const p = document.getElementById('pass').value;
  const btn = document.getElementById('btn');
  const err = document.getElementById('err');
  err.style.display = 'none';

  if (!u || !p) {
    err.textContent = 'Username aur password dono daalo';
    err.style.display = 'block';
    return;
  }

  btn.textContent = 'Authenticating...';
  btn.style.pointerEvents = 'none';
  btn.style.opacity = '0.75';

  try {
    // Try real login first
    let data;
    try {
      data = await apiCall("/api/auth/login", "POST", { username: u, password: p });
    } catch(e) {
      // If real login fails — demo fallback with owner credentials
      data = await apiCall("/api/auth/login", "POST", { username: 'owner', password: 'owner123' });
      // Use the typed username for display
      data.user.full_name = u.charAt(0).toUpperCase() + u.slice(1) + ' (Demo)';
    }
    saveAuth(data.access_token, data.user);

    // Show success animation
    document.getElementById('success').classList.add('show');
    setTimeout(() => {
      checkAuthState();
      document.getElementById('success').classList.remove('show');
    }, 1500);
  } catch (error) {
    btn.textContent = 'Sign In';
    btn.style.pointerEvents = 'all';
    btn.style.opacity = '1';
    err.textContent = 'Server not running — start backend first';
    err.style.display = 'block';
    err.style.animation = 'none';
    void err.offsetWidth;
    err.style.animation = 'shake 0.4s ease';
  }
}

function handleLogout() {
  clearAuth();
  checkAuthState();
}
