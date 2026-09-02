const API_BASE_URLS = ["/api"];

const MAX_ATTEMPTS = 5;
const LOCKOUT_MINUTES = 5;
const LOCKOUT_STORAGE_KEY = "dbshieldLoginLockout";

const form = document.querySelector(".login-form");
const usernameInput = document.querySelector("#log-username");
const passwordInput = document.querySelector("#log-pass");
const message = document.querySelector("#login-message");
const submitButton = document.querySelector("#SignInBtn");

let countdownTimer = null;

function setMessage(text, type = "error") {
  message.textContent = text;
  message.classList.toggle("form-message--success", type === "success");
  message.classList.toggle("form-message--locked", type === "locked");
}

function readLockoutState() {
  try {
    const raw = localStorage.getItem(LOCKOUT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : { attempts: 0, lockedUntil: null };
  } catch {
    return { attempts: 0, lockedUntil: null };
  }
}

function writeLockoutState(state) {
  try {
    localStorage.setItem(LOCKOUT_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // If storage is unavailable (private browsing, quota, etc.) the
    // lockout simply won't persist across reloads — fail open on storage,
    // not on security messaging.
  }
}

function clearCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

function setFormDisabled(disabled) {
  usernameInput.disabled = disabled;
  passwordInput.disabled = disabled;
  submitButton.disabled = disabled;
}

function formatRemaining(ms) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function showLockoutScreen(lockedUntil) {
  clearCountdown();
  setFormDisabled(true);

  function tick() {
    const remainingMs = lockedUntil - Date.now();
    if (remainingMs <= 0) {
      clearCountdown();
      writeLockoutState({ attempts: 0, lockedUntil: null });
      setFormDisabled(false);
      setMessage("You can try signing in again.", "error");
      return;
    }
    setMessage(
      `Too many failed attempts. Account locked. Try again in ${formatRemaining(remainingMs)}.`,
      "locked"
    );
  }

  tick();
  countdownTimer = setInterval(tick, 1000);
}

function checkLockoutOnLoad() {
  const state = readLockoutState();
  if (state.lockedUntil && state.lockedUntil > Date.now()) {
    showLockoutScreen(state.lockedUntil);
  }
}

function registerFailedAttempt() {
  const state = readLockoutState();
  const attempts = (state.attempts || 0) + 1;

  if (attempts >= MAX_ATTEMPTS) {
    const lockedUntil = Date.now() + LOCKOUT_MINUTES * 60 * 1000;
    writeLockoutState({ attempts: 0, lockedUntil });
    showLockoutScreen(lockedUntil);
    return { locked: true };
  }

  writeLockoutState({ attempts, lockedUntil: null });
  return { locked: false, remaining: MAX_ATTEMPTS - attempts };
}

function registerSuccessfulAttempt() {
  writeLockoutState({ attempts: 0, lockedUntil: null });
}

async function postLogin(username, password) {
  let lastError;

  for (const apiBaseUrl of API_BASE_URLS) {
    try {
      const response = await fetch(`${apiBaseUrl}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const payload = await response.json().catch(() => ({}));
      return { ok: response.ok, status: response.status, payload };
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`${lastError?.message || "Load failed"}. Check that you opened the app through http://127.0.0.1:5000/.`);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const currentLock = readLockoutState();
  if (currentLock.lockedUntil && currentLock.lockedUntil > Date.now()) {
    showLockoutScreen(currentLock.lockedUntil);
    return;
  }

  setMessage("");
  submitButton.disabled = true;
  submitButton.textContent = "Signing in...";

  try {
    const { ok, status, payload } = await postLogin(usernameInput.value.trim(), passwordInput.value);

    if (ok) {
      registerSuccessfulAttempt();
      sessionStorage.setItem("dbshieldUser", JSON.stringify(payload.user));
      setMessage(payload.message || "Login successful", "success");

      const target = payload.user.role === "admin"
        ? "../../dashboard/admin-dashboard.html"
        : "../../dashboard/staff-dashboard.html";
      window.location.href = target;
      return;
    }

    // Only count genuine invalid-credential responses toward the
    // lockout, not server errors or other unrelated failures.
    if (status === 401) {
      const result = registerFailedAttempt();
      if (!result.locked) {
        setMessage(
          `${payload.message || "Invalid credentials"}. ${result.remaining} attempt(s) remaining before lockout.`
        );
      }
      return;
    }

    setMessage(payload.message || `Login failed (${status})`);
  } catch (error) {
    setMessage(error.message || "Could not connect to DBShield backend");
  } finally {
    if (submitButton.textContent === "Signing in...") {
      submitButton.disabled = false;
      submitButton.textContent = "Sign In";
    }
  }
});

checkLockoutOnLoad();