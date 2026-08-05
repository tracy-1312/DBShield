const API_BASE_URLS = ["/api"];

const form = document.querySelector(".login-form");
const usernameInput = document.querySelector("#log-username");
const passwordInput = document.querySelector("#log-pass");
const message = document.querySelector("#login-message");
const submitButton = document.querySelector("#SignInBtn");

function setMessage(text, type = "error") {
  message.textContent = text;
  message.classList.toggle("form-message--success", type === "success");
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
      if (!response.ok) {
        throw new Error(payload.message || `Login failed (${response.status})`);
      }

      return payload;
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`${lastError?.message || "Load failed"}. Check that you opened the app through http://127.0.0.1:5000/.`);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("");
  submitButton.disabled = true;
  submitButton.textContent = "Signing in...";

  try {
    const payload = await postLogin(usernameInput.value.trim(), passwordInput.value);
    sessionStorage.setItem("dbshieldUser", JSON.stringify(payload.user));
    setMessage(payload.message || "Login successful", "success");

    const target = payload.user.role === "admin"
      ? "../../dashboard/admin-dashboard.html"
      : "../../dashboard/staff-dashboard.html";
    window.location.href = target;
  } catch (error) {
    setMessage(error.message || "Could not connect to DBShield backend");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Sign In";
  }
});
