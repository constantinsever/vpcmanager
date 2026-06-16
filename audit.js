const API_BASE_URL = window.APP_CONFIG.apiBaseUrl;

window.onload = function () {
  const token = localStorage.getItem("access_token");

  if (!token || isTokenExpired(token)) {
    logout();
    return;
  }

  loadAudit();
};

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp <= Math.floor(Date.now() / 1000);
  } catch {
    return true;
  }
}

function setMessage(message) {
  document.getElementById("auditMessage").textContent = message;
}

function goToDashboard() {
  window.location.href = "dashboard.html";
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("id_token");
  window.location.href = "index.html";
}

async function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem("id_token") || localStorage.getItem("access_token");

  return fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`
    }
  });
}

async function loadAudit() {
  setMessage("Loading events...");

  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/audit`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || data.error || "Failed to load events");
    }

    renderAuditTable(data);
    setMessage(`Loaded ${data.length} event(s).`);

  } catch (error) {
    setMessage("Failed to load events: " + error.message);
  }
}

function renderAuditTable(items) {
  const tbody = document.getElementById("auditTableBody");
  tbody.innerHTML = "";

  const sortedItems = [...items].sort((a, b) => {
    return new Date(b.event_time || 0) - new Date(a.event_time || 0);
  });

  sortedItems.forEach(item => {
    const row = document.createElement("tr");

    if (item.event_type === "DELETE") {
      row.classList.add("delete-event");
    }

    row.innerHTML = `
      <td>${escapeHtml(formatEventTime(item.event_time))}</td>
      <td>${escapeHtml(item.event_type || "")}</td>
      <td>${escapeHtml(item.resource_type || "")}</td>
      <td>${escapeHtml(item.name || "")}</td>
      <td>${escapeHtml(item.resource_id || "")}</td>
      <td>${escapeHtml(item.cidr || "")}</td>
      <td>${escapeHtml(item.region || "")}</td>
      <td>${escapeHtml(item.username || "")}</td>
    `;

    tbody.appendChild(row);
  });
}

function formatEventTime(value) {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  const ss = String(date.getSeconds()).padStart(2, "0");

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();

  return `${hh}:${mm}:${ss} / ${day}/${month}/${year}`;
}

async function clearAudit() {
  if (!confirm("Clear all VPC Manager events?")) {
    return;
  }

  setMessage("Clearing events...");

  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/audit`, {
      method: "DELETE"
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Failed to clear events:", data);
      //generare exceptie pentru a fi prinsa in catch si afisata un mesaj user-friendly
      throw new Error("Please contact application support.");
      
    }

    renderAuditTable([]);
    setMessage(`Cleared ${data.deleted_count} event(s).`);

  } catch (error) {
    //procesare exceptie ... afisare mesaj user-friendly
    setMessage("Failed to clear events: " + error.message);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}