// ─── Configuración base ─────────────────────────────────────────────────────
const API_BASE = ""; // URLs relativas — funciona en cualquier host/puerto

// ─── Toast notifications ────────────────────────────────────────────────────
function showToast(message, type = "info", duration = 3500) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = "0"; toast.style.transform = "translateX(120%)"; toast.style.transition = ".3s"; setTimeout(() => toast.remove(), 300); }, duration);
}

// ─── API helper ─────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    localStorage.clear();
    window.location.href = "/index.html";
    throw new Error("Sesión expirada");
  }

  if (!res.ok) {
    let errMsg = `Error ${res.status}`;
    try {
      const err = await res.json();
      errMsg = err.detail || JSON.stringify(err);
    } catch {}
    throw new Error(errMsg);
  }

  if (res.status === 204) return null;
  return res.json();
}

// ─── Auth helpers ────────────────────────────────────────────────────────────
function getUser() {
  try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
}

function requireAuth(allowedRoles = null) {
  document.documentElement.style.visibility = "hidden";
  const token = localStorage.getItem("token");
  const user = getUser();
  if (!token || !user) {
    window.location.replace("/index.html");
    return null;
  }
  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    const homeByRole = { solicitante: "/solicitudes.html", bodeguero: "/bodega.html", coordinador: "/dashboard.html" };
    window.location.replace(homeByRole[user.rol] || "/index.html");
    return null;
  }
  document.documentElement.style.visibility = "";
  return user;
}

// ─── Formateo ────────────────────────────────────────────────────────────────
function fmtMoney(n) {
  return "$" + Number(n || 0).toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-CL", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function fmtDatetime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-CL", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function estadoBadge(estado) {
  const labels = { pendiente: "Pendiente", aprobada: "Aprobada", rechazada: "Rechazada", entregada: "Entregada" };
  return `<span class="badge badge-${estado}">${labels[estado] || estado}</span>`;
}

function stockBadge(estado) {
  const labels = { normal: "Normal", bajo: "Stock Bajo", sin_stock: "Sin Stock" };
  return `<span class="badge badge-${estado}">${labels[estado] || estado}</span>`;
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function initSidebar(activePage) {
  const user = getUser();
  if (!user) return;

  // Inyectar info del usuario
  const nameEl = document.getElementById("sidebar-username");
  const roleEl = document.getElementById("sidebar-userrole");
  if (nameEl) nameEl.textContent = user.nombre;
  if (roleEl) roleEl.textContent = user.rol;

  // Marcar enlace activo
  document.querySelectorAll(".nav-link").forEach(link => {
    if (link.dataset.page === activePage) link.classList.add("active");
  });

  // Mostrar/ocultar según rol
  document.querySelectorAll("[data-roles]").forEach(el => {
    const roles = el.dataset.roles.split(",");
    if (!roles.includes(user.rol)) el.style.display = "none";
  });

  // Logout
  document.getElementById("btn-logout")?.addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "/index.html";
  });
}
