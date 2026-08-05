const records = [
  {
    id: "PT-00123",
    name: "John Smith",
    dob: "1985-03-15",
    category: "General",
    classification: "Level 2",
    access: "permitted"
  },
  {
    id: "PT-00456",
    name: "Sarah Johnson",
    dob: "1992-07-22",
    category: "Cardiology",
    classification: "Level 1",
    access: "permitted"
  },
  {
    id: "PT-00789",
    name: "Michael Brown",
    dob: "1978-11-30",
    category: "Oncology",
    classification: "Level 3 (Elevated Clearance - Oncology Department)",
    access: "restricted"
  },
  {
    id: "PT-00234",
    name: "Emily Davis",
    dob: "2001-05-18",
    category: "Pediatrics",
    classification: "Level 1",
    access: "permitted"
  },
  {
    id: "PT-00567",
    name: "Robert Wilson",
    dob: "1965-09-10",
    category: "Neurology",
    classification: "Level 4 (Restricted)",
    access: "restricted"
  }
];

let accessFilter = "all";

function wrapId(id) {
  return id.replace("-", "-<br>");
}

function actionCell(record) {
  if (record.access === "permitted") {
    return `
      <a class="action-button action-button--view" href="record-detail.html" aria-label="View ${record.name}">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        View
      </a>
    `;
  }

  return `
    <button class="action-button action-button--locked" type="button" aria-label="${record.name} locked">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="5" y="11" width="14" height="10" rx="2"></rect>
        <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
      </svg>
      Locked
    </button>
  `;
}

function renderSearchResults() {
  const body = document.querySelector("#records-body");
  if (!body) {
    return;
  }

  const query = document.querySelector("#record-search").value.trim().toLowerCase();
  const filtered = records.filter((record) => {
    const matchesQuery = !query || [
      record.id,
      record.name,
      record.dob,
      record.category,
      record.classification,
      record.access
    ].join(" ").toLowerCase().includes(query);

    const matchesAccess = accessFilter === "all" || record.access === accessFilter;
    return matchesQuery && matchesAccess;
  });

  body.innerHTML = filtered.map((record) => `
    <tr>
      <td><a class="patient-link" href="record-detail.html">${wrapId(record.id)}</a></td>
      <td>${record.name.replace(" ", "<br>")}</td>
      <td>${record.dob.replaceAll("-", "-<br>")}</td>
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

  document.querySelector("#results-count").textContent = `${filtered.length} ${filtered.length === 1 ? "record" : "records"} found`;
}

if (document.body.dataset.page === "search") {
  document.querySelector("#record-search").addEventListener("input", renderSearchResults);
  document.querySelector("#search-button").addEventListener("click", renderSearchResults);

  document.querySelectorAll("[data-access-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      accessFilter = button.dataset.accessFilter;
      document.querySelectorAll("[data-access-filter]").forEach((item) => {
        item.classList.toggle("chip--active", item === button);
      });
      renderSearchResults();
    });
  });

  renderSearchResults();
}
