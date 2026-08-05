const API_BASE_URLS = ["/api"];

let accessFilter = "all";
let levelFilter = "all";
let latestRecords = [];
let currentDetailRecord = null;
let detailEditMode = false;

function currentUser() {
  try {
    return JSON.parse(sessionStorage.getItem("dbshieldUser") || "null");
  } catch {
    return null;
  }
}

function updateSidebarUserLevel(user = currentUser()) {
  const levelElement = document.querySelector("#sidebar-user-level");
  if (!levelElement) return;

  if (user?.clearance_level) {
    levelElement.textContent = `Clearance Level ${user.clearance_level}`;
  } else {
    levelElement.textContent = "Clearance Level -";
  }
}

async function syncCurrentUserDisplay() {
  updateSidebarUserLevel();

  try {
    const payload = await fetchJson("/me");
    if (payload.user) {
      sessionStorage.setItem("dbshieldUser", JSON.stringify(payload.user));
      updateSidebarUserLevel(payload.user);
    }
  } catch {
    updateSidebarUserLevel();
  }
}

function wrapId(id) {
  return String(id).replace("-", "-<br>");
}

function wrapName(name) {
  return String(name || "").replace(" ", "<br>");
}

function wrapDate(date) {
  return String(date || "").replaceAll("-", "-<br>");
}

function apiErrorRow(message, colspan = 7) {
  return `<tr><td colspan="${colspan}" class="table-message">${message}</td></tr>`;
}

async function fetchJson(path, options = {}) {
  let lastError;

  for (const apiBaseUrl of API_BASE_URLS) {
    try {
      const response = await fetch(`${apiBaseUrl}${path}`, {
        credentials: "include",
        ...options,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.message || `Request failed (${response.status})`);
      }
      return payload;
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`${lastError?.message || "Load failed"}. Check that you opened the app through http://127.0.0.1:5000/.`);
}

function patientCell(record) {
  if (record.access === "permitted") {
    return `
      <a class="patient-link" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}">${wrapId(record.patient_id)}</a>
    `;
  }

  return `
    <span class="patient-link patient-link--locked" title="Restricted record">${wrapId(record.patient_id)}</span>
  `;
}

function actionCell(record) {
  if (record.access === "permitted") {
    return `
      <a class="action-button action-button--view" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}" aria-label="View ${record.full_name}">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        View
      </a>
    `;
  }

  return `
    <button class="action-button action-button--locked" type="button" aria-label="${record.full_name} locked">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="5" y="11" width="14" height="10" rx="2"></rect>
        <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
      </svg>
      Locked
    </button>
  `;
}

function adminActionCell(record) {
  return `
    <a class="action-button action-button--view" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}" aria-label="View or edit ${record.full_name}">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
      View/Edit
    </a>
  `;
}

function renderStaffRows(records) {
  const body = document.querySelector("#records-body");
  const filtered = records.filter((record) => accessFilter === "all" || record.access === accessFilter);

  if (!filtered.length) {
    body.innerHTML = apiErrorRow("No accessible records found for this filter.");
  } else {
    body.innerHTML = filtered.map((record) => `
      <tr>
        <td>${patientCell(record)}</td>
        <td>${wrapName(record.full_name)}</td>
        <td>${wrapDate(record.date_of_birth)}</td>
        <td>${record.category}</td>
        <td>${record.classification}</td>
        <td>
          <span class="access-pill access-pill--${record.access}">
            ${record.access === "permitted" ? "✓ Permitted" : "× Restricted"}
          </span>
        </td>
        <td>${actionCell(record)}</td>
      </tr>
    `).join("");
  }

  document.querySelector("#results-count").textContent = `${filtered.length} ${filtered.length === 1 ? "record" : "records"} found`;
}

async function loadStaffSearchResults() {
  const body = document.querySelector("#records-body");
  const query = document.querySelector("#record-search").value.trim();
  body.innerHTML = apiErrorRow("Loading records...");

  try {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    const payload = await fetchJson(`/search?${params}`);
    latestRecords = payload.data || [];
    renderStaffRows(latestRecords);
  } catch (error) {
    latestRecords = [];
    body.innerHTML = apiErrorRow(`${error.message}. Please sign in and make sure the backend is running.`);
    document.querySelector("#results-count").textContent = "0 records found";
  }
}

function renderAdminRows(records) {
  const body = document.querySelector("#records-body");
  const filtered = records.filter((record) => {
    return levelFilter === "all" || record.classification_level === Number(levelFilter);
  });

  if (!filtered.length) {
    body.innerHTML = apiErrorRow("No records found for this filter.");
  } else {
    body.innerHTML = filtered.map((record) => `
      <tr>
        <td><a class="patient-link" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}">${wrapId(record.patient_id)}</a></td>
        <td>${wrapName(record.full_name)}</td>
        <td>${wrapDate(record.date_of_birth)}</td>
        <td>${record.category}</td>
        <td>
          <span class="access-pill access-pill--level-${record.classification_level}">
            Level ${record.classification_level}
          </span>
        </td>
        <td>${record.assigned_doctor}</td>
        <td>${adminActionCell(record)}</td>
      </tr>
    `).join("");
  }

  document.querySelector("#results-count").textContent = `${filtered.length} ${filtered.length === 1 ? "record" : "records"} found`;
}

async function loadAdminSearchResults() {
  const body = document.querySelector("#records-body");
  const query = document.querySelector("#record-search").value.trim();
  body.innerHTML = apiErrorRow("Loading records...");

  try {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    const payload = await fetchJson(`/search?${params}`);
    latestRecords = payload.data || [];
    renderAdminRows(latestRecords);
  } catch (error) {
    latestRecords = [];
    body.innerHTML = apiErrorRow(`${error.message}. Please sign in as an admin and make sure the backend is running.`);
    document.querySelector("#results-count").textContent = "0 records found";
  }
}

async function logout() {
  try {
    await fetchJson(`/logout`, { method: "POST" });
  } catch {
    // If the backend is already stopped, still clear the local browser state.
  }
  sessionStorage.removeItem("dbshieldUser");
  window.location.href = "../auth/sign_in/index.html";
}

function wireLogoutLinks() {
  document.querySelectorAll(".logout a, a.logout").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      logout();
    });
  });
}

function setField(selector, value) {
  const element = document.querySelector(selector);
  if (element) {
    element.value = value || "";
  }
}

const editableDetailSelectors = [
  "#detail-full-name",
  "#detail-dob",
  "#detail-contact",
  "#detail-email",
  "#detail-doctor",
  "#detail-department",
  "#detail-notes",
];

function setDetailMessage(message, tone = "neutral") {
  const element = document.querySelector("#detail-edit-message");
  if (!element) return;
  element.textContent = message;
  element.dataset.tone = tone;
}

function detailPayload() {
  return {
    full_name: document.querySelector("#detail-full-name").value.trim(),
    date_of_birth: document.querySelector("#detail-dob").value.trim(),
    contact_number: document.querySelector("#detail-contact").value.trim(),
    email: document.querySelector("#detail-email").value.trim(),
    assigned_doctor: document.querySelector("#detail-doctor").value.trim(),
    category: document.querySelector("#detail-department").value.trim(),
    medical_notes: document.querySelector("#detail-notes").value.trim(),
  };
}

function setDetailEditMode(enabled) {
  detailEditMode = enabled;
  document.body.classList.toggle("is-editing-detail", enabled);
  editableDetailSelectors.forEach((selector) => {
    const field = document.querySelector(selector);
    if (field) field.readOnly = !enabled;
  });

  const button = document.querySelector("#detail-edit-button");
  if (button) {
    button.innerHTML = enabled ? `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 6 9 17l-5-5"></path>
      </svg>
      Save
    ` : `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 20h9"></path>
        <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"></path>
      </svg>
      Edit
    `;
  }
}

function fillRecordDetail(record) {
  document.querySelector("#detail-subtitle").textContent = `${record.full_name} - ${record.patient_id}`;
  setField("#detail-patient-id", record.patient_id);
  setField("#detail-full-name", record.full_name);
  setField("#detail-dob", record.date_of_birth);
  setField("#detail-contact", record.contact_number);
  setField("#detail-email", record.email);
  setField("#detail-doctor", record.assigned_doctor);
  setField("#detail-department", record.category);
  setField("#detail-last-visit", record.last_modified ? record.last_modified.slice(0, 10) : "");
  setField("#detail-notes", record.medical_notes);
}

async function saveRecordDetail() {
  if (!currentDetailRecord) return;
  const button = document.querySelector("#detail-edit-button");
  if (button) button.disabled = true;
  setDetailMessage("Saving changes...", "neutral");

  try {
    const payload = await fetchJson(`/records/${encodeURIComponent(currentDetailRecord.patient_id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(detailPayload()),
    });
    currentDetailRecord = payload.record;
    fillRecordDetail(currentDetailRecord);
    setDetailEditMode(false);
    setDetailMessage("Changes saved.", "success");
  } catch (error) {
    setDetailMessage(error.message, "error");
  } finally {
    if (button) button.disabled = false;
  }
}

async function loadRecordDetail() {
  const params = new URLSearchParams(window.location.search);
  const patientId = params.get("id") || "PT-00123";

  try {
    const payload = await fetchJson(`/records/${encodeURIComponent(patientId)}`);
    const record = payload.record;
    const user = payload.user || currentUser();
    currentDetailRecord = record;

    document.querySelector("#portal-label").textContent = user?.role === "admin" ? "Admin Portal" : "Staff Portal";
    document.querySelector("#back-to-search").href = user?.role === "admin" ? "admin-search.html" : "staff-search.html";
    document.querySelector("#dashboard-link").href = user?.role === "admin" ? "admin-dashboard.html" : "staff-dashboard.html";

    fillRecordDetail(record);
    setDetailEditMode(false);

    const editButton = document.querySelector("#detail-edit-button");
    const canEdit = ["admin", "data_manager"].includes(user?.role) && record.access === "permitted";
    if (editButton) {
      editButton.hidden = !canEdit;
      editButton.addEventListener("click", () => {
        if (detailEditMode) {
          saveRecordDetail();
        } else {
          setDetailEditMode(true);
          setDetailMessage("Editing enabled. Save when finished.", "neutral");
        }
      }, { once: false });
    }
  } catch (error) {
    const subtitle = document.querySelector("#detail-subtitle");
    if (subtitle) subtitle.textContent = `${patientId} - ${error.message}`;
    const editButton = document.querySelector("#detail-edit-button");
    if (editButton) editButton.hidden = true;
  }
}


function managementMessage(selector, message, tone = "neutral") {
  const element = document.querySelector(selector);
  if (!element) return;
  element.textContent = message;
  element.dataset.tone = tone;
}

function roleDisplay(user) {
  return user.role_label || {
    admin: "Admin",
    data_manager: "Staff",
    viewer: "Specialist",
  }[user.role] || user.role;
}

function roleClass(user) {
  return (user.role || "staff").replace("_", "-");
}

function setUserFormOpen(open, mode = "create") {
  const card = document.querySelector("#add-user-card");
  if (!card) return;
  card.hidden = !open;
  document.querySelector("#user-form-title").textContent = mode === "edit" ? "Edit User" : "Add New User";
  document.querySelector("#user-submit-button").textContent = mode === "edit" ? "Save Changes" : "Create User";
  document.querySelector("#user-password").required = mode !== "edit";
  if (!open) {
    document.querySelector("#user-form").reset();
    document.querySelector("#user-id").value = "";
    managementMessage("#user-form-message", "");
  }
}

function userPayload() {
  const payload = {
    username: document.querySelector("#user-username").value.trim(),
    full_name: document.querySelector("#user-full-name").value.trim(),
    email: document.querySelector("#user-email").value.trim(),
    role: document.querySelector("#user-role").value,
    clearance_level: document.querySelector("#user-clearance").value,
  };
  const password = document.querySelector("#user-password").value;
  if (password) payload.password = password;
  return payload;
}

function fillUserForm(user) {
  document.querySelector("#user-id").value = user.user_id;
  document.querySelector("#user-username").value = user.username;
  document.querySelector("#user-full-name").value = user.full_name;
  document.querySelector("#user-email").value = user.email;
  document.querySelector("#user-role").value = user.role;
  document.querySelector("#user-clearance").value = user.clearance_level;
  document.querySelector("#user-password").value = "";
  setUserFormOpen(true, "edit");
  managementMessage("#user-form-message", "Leave password blank to keep the current password.");
}

function renderManagedUsers(users) {
  const body = document.querySelector("#users-body");
  if (!body) return;
  if (!users.length) {
    body.innerHTML = apiErrorRow("No users found.", 6);
  } else {
    body.innerHTML = users.map((user) => `
      <tr>
        <td><strong>${user.username}</strong></td>
        <td>${user.full_name}</td>
        <td>${user.email}</td>
        <td><span class="role-pill role-pill--${roleClass(user)}">${roleDisplay(user)}</span></td>
        <td>${user.classification || `Level ${user.clearance_level}`}</td>
        <td>
          <div class="management-actions">
            <button class="management-action management-action--edit" type="button" data-edit-user="${user.user_id}">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"></path></svg>
              Edit
            </button>
            <button class="management-action management-action--delete" type="button" data-delete-user="${user.user_id}">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v5"></path><path d="M14 11v5"></path></svg>
              Delete
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  }
  document.querySelector("#users-count").textContent = `${users.length} ${users.length === 1 ? "user" : "users"}`;

  document.querySelectorAll("[data-edit-user]").forEach((button) => {
    button.addEventListener("click", () => {
      const user = users.find((item) => item.user_id === Number(button.dataset.editUser));
      if (user) fillUserForm(user);
    });
  });

  document.querySelectorAll("[data-delete-user]").forEach((button) => {
    button.addEventListener("click", async () => {
      const user = users.find((item) => item.user_id === Number(button.dataset.deleteUser));
      if (!user || !confirm(`Delete user ${user.username}?`)) return;
      try {
        await fetchJson(`/admin/users/${user.user_id}`, { method: "DELETE" });
        await loadManagedUsers();
      } catch (error) {
        managementMessage("#user-form-message", error.message, "error");
      }
    });
  });
}

async function loadManagedUsers() {
  const body = document.querySelector("#users-body");
  if (body) body.innerHTML = apiErrorRow("Loading users...", 6);
  try {
    const payload = await fetchJson("/admin/users");
    renderManagedUsers(payload.data || []);
  } catch (error) {
    if (body) body.innerHTML = apiErrorRow(error.message, 6);
  }
}

function wireManageUsersPage() {
  document.querySelector("#add-user-toggle").addEventListener("click", () => setUserFormOpen(true, "create"));
  document.querySelector("#cancel-user-button").addEventListener("click", () => setUserFormOpen(false));
  document.querySelector("#cancel-user-x").addEventListener("click", () => setUserFormOpen(false));
  document.querySelector("#user-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const userId = document.querySelector("#user-id").value;
    const isEdit = Boolean(userId);
    const payload = userPayload();
    if (!isEdit && !payload.password) {
      managementMessage("#user-form-message", "Password is required for new users.", "error");
      return;
    }
    managementMessage("#user-form-message", isEdit ? "Saving user..." : "Creating user...");
    try {
      await fetchJson(isEdit ? `/admin/users/${userId}` : "/admin/users", {
        method: isEdit ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setUserFormOpen(false);
      await loadManagedUsers();
    } catch (error) {
      managementMessage("#user-form-message", error.message, "error");
    }
  });
  loadManagedUsers();
}

function setRecordFormOpen(open) {
  const card = document.querySelector("#add-record-card");
  if (!card) return;
  card.hidden = !open;
  if (!open) {
    document.querySelector("#record-form").reset();
    managementMessage("#record-form-message", "");
  }
}

function recordCreatePayload() {
  return {
    patient_id: document.querySelector("#record-patient-id").value.trim(),
    full_name: document.querySelector("#record-full-name").value.trim(),
    date_of_birth: document.querySelector("#record-dob").value,
    category: document.querySelector("#record-category").value.trim(),
    classification_level: document.querySelector("#record-classification").value,
    assigned_doctor: document.querySelector("#record-doctor").value.trim(),
    contact_number: document.querySelector("#record-contact").value.trim(),
    email: document.querySelector("#record-email").value.trim(),
    medical_notes: document.querySelector("#record-notes").value.trim(),
  };
}

function renderManagedRecords(records) {
  const body = document.querySelector("#managed-records-body");
  if (!body) return;
  if (!records.length) {
    body.innerHTML = apiErrorRow("No records found.", 7);
  } else {
    body.innerHTML = records.map((record) => `
      <tr>
        <td><a class="patient-link" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}">${wrapId(record.patient_id)}</a></td>
        <td>${wrapName(record.full_name)}</td>
        <td>${record.category}</td>
        <td><span class="access-pill access-pill--level-${record.classification_level}">${record.classification}</span></td>
        <td>${record.assigned_doctor}</td>
        <td>${record.last_modified ? record.last_modified.slice(0, 10) : "-"}</td>
        <td>
          <div class="management-actions">
            <a class="management-action management-action--edit" href="staff-search-record-detail.html?id=${encodeURIComponent(record.patient_id)}">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"></path></svg>
              Edit
            </a>
            <button class="management-action management-action--delete" type="button" data-delete-record="${record.patient_id}">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v5"></path><path d="M14 11v5"></path></svg>
              Delete
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  }
  document.querySelector("#managed-records-count").textContent = `${records.length} ${records.length === 1 ? "record" : "records"}`;

  document.querySelectorAll("[data-delete-record]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!confirm(`Delete record ${button.dataset.deleteRecord}?`)) return;
      try {
        await fetchJson(`/admin/records/${encodeURIComponent(button.dataset.deleteRecord)}`, { method: "DELETE" });
        await loadManagedRecords();
      } catch (error) {
        managementMessage("#record-form-message", error.message, "error");
      }
    });
  });
}

async function loadManagedRecords() {
  const body = document.querySelector("#managed-records-body");
  if (body) body.innerHTML = apiErrorRow("Loading records...", 7);
  try {
    const payload = await fetchJson("/admin/records");
    renderManagedRecords(payload.data || []);
  } catch (error) {
    if (body) body.innerHTML = apiErrorRow(error.message, 7);
  }
}

function wireManageDataPage() {
  document.querySelector("#add-record-toggle").addEventListener("click", () => setRecordFormOpen(true));
  document.querySelector("#cancel-record-button").addEventListener("click", () => setRecordFormOpen(false));
  document.querySelector("#cancel-record-x").addEventListener("click", () => setRecordFormOpen(false));
  document.querySelector("#record-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    managementMessage("#record-form-message", "Creating record...");
    try {
      await fetchJson("/admin/records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recordCreatePayload()),
      });
      setRecordFormOpen(false);
      await loadManagedRecords();
    } catch (error) {
      managementMessage("#record-form-message", error.message, "error");
    }
  });
  loadManagedRecords();
}

wireLogoutLinks();
syncCurrentUserDisplay();

if (document.body.dataset.page === "search") {
  document.querySelector("#record-search").addEventListener("input", loadStaffSearchResults);
  document.querySelector("#search-button").addEventListener("click", loadStaffSearchResults);

  document.querySelectorAll("[data-access-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      accessFilter = button.dataset.accessFilter;
      document.querySelectorAll("[data-access-filter]").forEach((item) => {
        item.classList.toggle("chip--active", item === button);
      });
      renderStaffRows(latestRecords);
    });
  });

  loadStaffSearchResults();
}

if (document.body.dataset.page === "admin-search") {
  document.querySelector("#record-search").addEventListener("input", loadAdminSearchResults);
  document.querySelector("#search-button").addEventListener("click", loadAdminSearchResults);

  document.querySelectorAll("[data-level-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      levelFilter = button.dataset.levelFilter;
      document.querySelectorAll("[data-level-filter]").forEach((item) => {
        item.classList.toggle("chip--active", item === button);
      });
      renderAdminRows(latestRecords);
    });
  });

  loadAdminSearchResults();
}


if (document.body.dataset.page === "admin-users") {
  wireManageUsersPage();
}

if (document.body.dataset.page === "admin-data") {
  wireManageDataPage();
}

if (document.body.dataset.page === "detail") {
  loadRecordDetail();
}
