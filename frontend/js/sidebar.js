// Genera el HTML del sidebar e inicializa comportamiento
function renderSidebar(activePage) {
  const sidebarEl = document.getElementById("app-sidebar");
  if (!sidebarEl) return;

  sidebarEl.innerHTML = `
    <div class="sidebar-logo">
      <div class="logo-icon">N</div>
      <div>
        <div class="logo-text">Novum GLP</div>
        <div class="logo-sub">Gestión de Materiales</div>
      </div>
    </div>
    <div class="sidebar-user">
      <div class="user-name" id="sidebar-username">—</div>
      <div class="user-role" id="sidebar-userrole">—</div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section" data-roles="coordinador">Principal</div>
      <a href="/dashboard.html" class="nav-link" data-page="dashboard" data-roles="coordinador">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        Dashboard
      </a>

      <div class="nav-section" data-roles="solicitante">Solicitudes</div>
      <a href="/solicitudes.html" class="nav-link" data-page="solicitudes" data-roles="solicitante">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        Mis Solicitudes
      </a>
      <a href="/nueva-solicitud.html" class="nav-link" data-page="nueva-solicitud" data-roles="solicitante">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Nueva Solicitud
      </a>

      <div class="nav-section" data-roles="coordinador">Coordinación</div>
      <a href="/aprobaciones.html" class="nav-link" data-page="aprobaciones" data-roles="coordinador">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
        Aprobaciones
      </a>
      <a href="/materiales.html" class="nav-link" data-page="materiales" data-roles="coordinador,bodeguero">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
        Materiales
      </a>

      <div class="nav-section" data-roles="bodeguero">Bodega</div>
      <a href="/bodega.html" class="nav-link" data-page="bodega" data-roles="bodeguero">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
        Despacho
      </a>

      <div class="nav-section" data-roles="coordinador,bodeguero">Reportes</div>
      <a href="/reportes.html" class="nav-link" data-page="reportes" data-roles="coordinador,bodeguero">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
        Reportes
      </a>
      <a href="/alertas.html" class="nav-link" data-page="alertas" data-roles="coordinador,bodeguero">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
        Alertas de Stock
        <span class="nav-badge" id="alertas-badge" style="display:none"></span>
      </a>
    </nav>
    <div class="sidebar-footer">
      <button class="btn-logout" id="btn-logout">
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
        Cerrar sesión
      </button>
    </div>
  `;

  initSidebar(activePage);
}
