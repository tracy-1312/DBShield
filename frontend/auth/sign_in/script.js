// Map backend roles to the dashboard each one should land on.
// Adjust these paths to match where your dashboard files actually live.
const ROLE_REDIRECTS = {
  admin: "../../dashboard/admin-dashboard.html",
  data_manager: "../../dashboard/staff-dashboard.html",
  viewer: "../../dashboard/staff-dashboard.html",
};

const form = document.getElementById("login-form");
const errorEl = document.getElementById("login-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault(); // stop the browser from doing a normal form POST/redirect

  const username = document.getElementById("log-username").value.trim();
  const password = document.getElementById("log-pass").value;

  errorEl.style.display = "none";

  if (!username || !password) {
    errorEl.textContent = "Please enter both username and password.";
    errorEl.style.display = "block";
    return;
  }

  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // credentials: "include" is required if index.html and app.py are served
      // from different origins/ports, so the session cookie gets sent/stored.
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok || data.status !== "success") {
      errorEl.textContent = data.message || "Invalid credentials.";
      errorEl.style.display = "block";
      return;
    }

    const destination = ROLE_REDIRECTS[data.role];

    if (destination) {
      window.location.href = destination;
    } else {
      errorEl.textContent = `Unrecognized role "${data.role}". Contact an administrator.`;
      errorEl.style.display = "block";
    }
  } catch (err) {
    errorEl.textContent = "Could not reach the server. Please try again.";
    errorEl.style.display = "block";
  }
});