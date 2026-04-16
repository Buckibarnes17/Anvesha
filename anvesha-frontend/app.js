const DEFAULT_API_BASE = localStorage.getItem("anvesha.apiBase") || "http://127.0.0.1:8000/v1";

const state = {
  apiBase: DEFAULT_API_BASE,
  projects: [],
  traces: [],
  selectedProject: null,
  selectedTrace: null,
  selectedSpanId: null,
  collapsedSpans: new Set(),
  filters: {
    project: "",
    trace: "",
    span: "",
  },
  ui: {
    view: "projects",
    activeTab: "attributes",
  },
};

const els = {
  endpointForm: document.querySelector("#endpoint-form"),
  endpointInput: document.querySelector("#endpoint-input"),
  refreshButton: document.querySelector("#refresh-button"),
  connectionBadge: document.querySelector("#connection-badge"),
  navProjectCount: document.querySelector("#nav-project-count"),
  breadcrumb: document.querySelector("#breadcrumb"),
  globalSearch: document.querySelector("#global-search"),
  projectsView: document.querySelector("#projects-view"),
  projectView: document.querySelector("#project-view"),
  traceView: document.querySelector("#trace-view"),
  traceSearch: document.querySelector("#trace-search"),
  spanSearch: document.querySelector("#span-search"),
  totalProjects: document.querySelector("#total-projects"),
  totalTraces: document.querySelector("#total-traces"),
  totalSpans: document.querySelector("#total-spans"),
  latestActivity: document.querySelector("#latest-activity"),
  projectsGrid: document.querySelector("#projects-grid"),
  backToProjects: document.querySelector("#back-to-projects"),
  backToProject: document.querySelector("#back-to-project"),
  projectTitle: document.querySelector("#project-title"),
  projectTotalTraces: document.querySelector("#project-total-traces"),
  projectTotalSpans: document.querySelector("#project-total-spans"),
  projectErrorTraces: document.querySelector("#project-error-traces"),
  projectLastActivity: document.querySelector("#project-last-activity"),
  traceTableBody: document.querySelector("#trace-table-body"),
  traceTitle: document.querySelector("#trace-title"),
  traceStatus: document.querySelector("#trace-status"),
  traceLatency: document.querySelector("#trace-latency"),
  traceSpanCount: document.querySelector("#trace-span-count"),
  traceMeta: document.querySelector("#trace-meta"),
  spanTree: document.querySelector("#span-tree"),
  selectedSpanTitle: document.querySelector("#selected-span-title"),
  selectedSpanKind: document.querySelector("#selected-span-kind"),
  selectedSpanStatus: document.querySelector("#selected-span-status"),
  selectedSpanLatency: document.querySelector("#selected-span-latency"),
  selectedSpanStart: document.querySelector("#selected-span-start"),
  selectedSpanParent: document.querySelector("#selected-span-parent"),
  selectedSpanAttributes: document.querySelector("#selected-span-attributes"),
  selectedSpanEvents: document.querySelector("#selected-span-events"),
  selectedSpanRaw: document.querySelector("#selected-span-raw"),
  detailTabs: [...document.querySelectorAll(".detail-tab")],
  detailPanels: [...document.querySelectorAll(".detail-tab-panel")],
  projectCardTemplate: document.querySelector("#project-card-template"),
  traceRowTemplate: document.querySelector("#trace-row-template"),
  spanNodeTemplate: document.querySelector("#span-node-template"),
};

function setConnectionStatus(label, mode) {
  els.connectionBadge.textContent = label;
  els.connectionBadge.className = `connection-badge ${mode ? `status-${mode}` : ""}`.trim();
}

function fmtNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}

function fmtDate(value) {
  if (!value) return "No data";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function fmtDuration(value) {
  if (value == null || Number.isNaN(Number(value))) return "--";
  const ms = Number(value);
  if (ms < 1000) return `${ms.toFixed(1)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatScalar(value) {
  if (value == null) return '<span class="field-empty">--</span>';
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (typeof value === "string") return escapeHtml(value);
  return escapeHtml(JSON.stringify(value));
}

function renderStructuredValue(label, value, depth = 0) {
  if (value == null || typeof value !== "object") {
    return `
      <div class="field-row" style="--field-depth:${depth}">
        <div class="field-key">${escapeHtml(label)}</div>
        <div class="field-value">${formatScalar(value)}</div>
      </div>
    `;
  }

  if (Array.isArray(value)) {
    if (!value.length) {
      return `
        <div class="field-group" style="--field-depth:${depth}">
          <div class="field-group-title">${escapeHtml(label)}</div>
          <div class="field-empty">No items</div>
        </div>
      `;
    }

    const items = value
      .map((item, index) => renderStructuredValue(`${label} [${index}]`, item, depth + 1))
      .join("");
    return `
      <div class="field-group" style="--field-depth:${depth}">
        <div class="field-group-title">${escapeHtml(label)}</div>
        <div class="field-group-body">${items}</div>
      </div>
    `;
  }

  const entries = Object.entries(value);
  if (!entries.length) {
    return `
      <div class="field-group" style="--field-depth:${depth}">
        <div class="field-group-title">${escapeHtml(label)}</div>
        <div class="field-empty">No fields</div>
      </div>
    `;
  }

  return `
    <div class="field-group" style="--field-depth:${depth}">
      <div class="field-group-title">${escapeHtml(label)}</div>
      <div class="field-group-body">
        ${entries.map(([key, child]) => renderStructuredValue(key, child, depth + 1)).join("")}
      </div>
    </div>
  `;
}

function renderAttributesView(attributes) {
  const entries = Object.entries(attributes || {});
  if (!entries.length) {
    return '<div class="empty-state compact-empty">No attributes recorded.</div>';
  }
  return entries.map(([key, value]) => renderStructuredValue(key, value)).join("");
}

function renderEventsView(events) {
  if (!events?.length) {
    return '<div class="empty-state compact-empty">No events recorded.</div>';
  }

  return events
    .map((event, index) => {
      const attrs = Object.entries(event.attributes || {});
      return `
        <article class="event-card">
          <div class="event-card-header">
            <div>
              <h4>${escapeHtml(event.name || `Event ${index + 1}`)}</h4>
              <p>${escapeHtml(fmtDate(event.timestamp))}</p>
            </div>
            <span class="meta-pill">${attrs.length} attrs</span>
          </div>
          <div class="event-card-body">
            ${
              attrs.length
                ? attrs.map(([key, value]) => renderStructuredValue(key, value, 0)).join("")
                : '<div class="field-empty">No attributes</div>'
            }
          </div>
        </article>
      `;
    })
    .join("");
}

function apiBaseHost() {
  try {
    return new URL(state.apiBase).host;
  } catch {
    return state.apiBase;
  }
}

async function apiGet(path) {
  const url = `${state.apiBase.replace(/\/$/, "")}${path}`;
  const response = await fetch(url);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }
  return response.json();
}

function showView(view) {
  state.ui.view = view;
  els.projectsView.classList.toggle("hidden", view !== "projects");
  els.projectView.classList.toggle("hidden", view !== "project");
  els.traceView.classList.toggle("hidden", view !== "trace");

  if (view === "projects") {
    els.breadcrumb.textContent = "Projects";
  } else if (view === "project") {
    els.breadcrumb.textContent = `Projects > ${state.selectedProject?.name || ""}`;
  } else {
    els.breadcrumb.textContent = `Projects > ${state.selectedProject?.name || ""} > Trace Details`;
  }
}

function renderSidebarCounts() {
  els.navProjectCount.textContent = fmtNumber(state.projects.length);
}

function renderProjectSummary() {
  const totalTraces = state.projects.reduce((sum, item) => sum + item.traceCount, 0);
  const totalSpans = state.projects.reduce((sum, item) => sum + item.spanCount, 0);
  const latest = [...state.projects]
    .map((item) => item.lastUpdatedAt)
    .filter(Boolean)
    .sort()
    .at(-1);

  els.totalProjects.textContent = fmtNumber(state.projects.length);
  els.totalTraces.textContent = fmtNumber(totalTraces);
  els.totalSpans.textContent = fmtNumber(totalSpans);
  els.latestActivity.textContent = latest ? fmtDate(latest) : "No data";
}

function renderProjectsGrid() {
  const term = (state.filters.project || state.filters.global || "").trim().toLowerCase();
  const items = state.projects.filter((project) => !term || project.name.toLowerCase().includes(term));
  els.projectsGrid.innerHTML = "";

  if (!items.length) {
    els.projectsGrid.innerHTML = `<div class="empty-state">No projects found.</div>`;
    return;
  }

  for (const project of items) {
    const fragment = els.projectCardTemplate.content.cloneNode(true);
    const button = fragment.querySelector(".project-card");
    const status = project.traceCount ? "ACTIVE" : "EMPTY";
    button.querySelector(".project-card-name").textContent = project.name;
    button.querySelector(".project-card-subtitle").textContent =
      project.traceCount ? `Last activity ${fmtDate(project.lastUpdatedAt)}` : "No traces uploaded yet.";
    button.querySelector(".project-status-pill").textContent = status;
    button.querySelector(".project-card-traces").textContent = fmtNumber(project.traceCount);
    button.querySelector(".project-card-spans").textContent = fmtNumber(project.spanCount);
    button.addEventListener("click", () => openProject(project));
    els.projectsGrid.appendChild(fragment);
  }
}

function renderProjectView() {
  const project = state.selectedProject;
  els.projectTitle.textContent = project?.name || "Select a project";
  if (!project) {
    els.traceTableBody.innerHTML = "";
    return;
  }

  els.projectTotalTraces.textContent = fmtNumber(state.traces.length);
  els.projectTotalSpans.textContent = fmtNumber(
    state.traces.reduce((sum, trace) => sum + (trace.spanCount || 0), 0)
  );
  els.projectErrorTraces.textContent = fmtNumber(
    state.traces.filter((trace) => Number(trace.latencyMs || 0) > 0).length
  );
  els.projectLastActivity.textContent = project.lastUpdatedAt ? fmtDate(project.lastUpdatedAt) : "No data";

  const term = state.filters.trace.trim().toLowerCase();
  const rows = state.traces.filter((trace) => {
    return (
      !term ||
      trace.projectName?.toLowerCase().includes(term) ||
      trace.traceId.toLowerCase().includes(term) ||
      (trace.sessionId || "").toLowerCase().includes(term)
    );
  });

  els.traceTableBody.innerHTML = "";
  if (!rows.length) {
    els.traceTableBody.innerHTML = `<tr><td colspan="6" class="empty-table">No traces found.</td></tr>`;
    return;
  }

  for (const trace of rows) {
    const fragment = els.traceRowTemplate.content.cloneNode(true);
    const row = fragment.querySelector(".trace-row");
    const isSlow = Number(trace.latencyMs || 0) > 1000;
    row.querySelector(".trace-status-cell").innerHTML =
      `<span class="row-status-icon ${isSlow ? "status-error-dot" : "status-ok-dot"}"></span>`;
    row.querySelector(".trace-id-cell").textContent = trace.traceId;
    row.querySelector(".trace-session-cell").textContent = trace.sessionId || "--";
    row.querySelector(".trace-start-cell").textContent = fmtDate(trace.startTime);
    row.querySelector(".trace-count-cell").textContent = fmtNumber(trace.spanCount);
    row.querySelector(".trace-latency-cell").textContent = fmtDuration(trace.latencyMs);
    row.addEventListener("click", () => openTrace(trace.traceId));
    els.traceTableBody.appendChild(fragment);
  }
}

function buildTraceTree(trace) {
  const spans = [...(trace?.spans || [])].sort(
    (a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
  );
  const byId = new Map(spans.map((span) => [span.spanId, { ...span, children: [] }]));
  const roots = [];

  for (const span of byId.values()) {
    if (span.parentId && byId.has(span.parentId)) {
      byId.get(span.parentId).children.push(span);
    } else {
      roots.push(span);
    }
  }

  return { roots, byId };
}

function flattenTree(nodes, depth = 0, list = []) {
  for (const node of nodes) {
    list.push({ ...node, depth });
    if (!state.collapsedSpans.has(node.spanId)) {
      flattenTree(node.children, depth + 1, list);
    }
  }
  return list;
}

function renderTraceView() {
  const trace = state.selectedTrace;
  if (!trace) {
    els.traceTitle.textContent = "No trace selected";
    els.traceStatus.textContent = "--";
    els.traceLatency.textContent = "--";
    els.traceSpanCount.textContent = "0";
    els.traceMeta.innerHTML = "";
    els.spanTree.innerHTML = `<div class="empty-state">Select a trace.</div>`;
    renderSelectedSpan(null, null);
    return;
  }

  const tree = buildTraceTree(trace);
  const flat = flattenTree(tree.roots);
  const hasError = flat.some((span) => span.statusCode === "ERROR");

  els.traceTitle.textContent = trace.traceId;
  els.traceStatus.textContent = hasError ? "ERROR" : "OK";
  els.traceStatus.className = hasError ? "status-text-error" : "status-text-ok";
  els.traceLatency.textContent = fmtDuration(trace.latencyMs);
  els.traceSpanCount.textContent = fmtNumber(trace.spanCount);
  els.traceMeta.innerHTML = [
    `<span class="meta-pill">Project: ${state.selectedProject?.name || "--"}</span>`,
    `<span class="meta-pill">Session: ${trace.sessionId || "--"}</span>`,
    `<span class="meta-pill">Start: ${fmtDate(trace.startTime)}</span>`,
    `<span class="meta-pill">End: ${fmtDate(trace.endTime)}</span>`,
  ].join("");

  if (!state.selectedSpanId || !tree.byId.has(state.selectedSpanId)) {
    state.selectedSpanId = flat[0]?.spanId || null;
  }

  const term = state.filters.span.trim().toLowerCase();
  const visible = flat.filter((span) => {
    return (
      !term ||
      span.name.toLowerCase().includes(term) ||
      span.spanKind.toLowerCase().includes(term) ||
      span.spanId.toLowerCase().includes(term) ||
      span.statusCode.toLowerCase().includes(term)
    );
  });

  els.spanTree.innerHTML = "";
  for (const span of visible) {
    const fragment = els.spanNodeTemplate.content.cloneNode(true);
    const button = fragment.querySelector(".span-node");
    const toggle = button.querySelector(".span-toggle");
    const statusDot = button.querySelector(".status-dot");
    button.classList.toggle("active", state.selectedSpanId === span.spanId);
    button.style.setProperty("--depth", span.depth);
    button.querySelector(".span-name").textContent = span.name;
    button.querySelector(".span-events").textContent = `${fmtNumber((span.events || []).length)} events`;
    button.querySelector(".span-latency").textContent = fmtDuration(span.latencyMs);
    button.querySelector(".span-status").textContent = span.statusCode;
    statusDot.classList.add(span.statusCode === "ERROR" ? "status-error-dot" : "status-ok-dot");
    if (span.children.length) {
      toggle.textContent = state.collapsedSpans.has(span.spanId) ? "▸" : "▾";
      toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        if (state.collapsedSpans.has(span.spanId)) {
          state.collapsedSpans.delete(span.spanId);
        } else {
          state.collapsedSpans.add(span.spanId);
        }
        renderTraceView();
      });
    } else {
      toggle.textContent = "•";
      toggle.classList.add("leaf-toggle");
    }
    button.addEventListener("click", () => {
      state.selectedSpanId = span.spanId;
      renderTraceView();
    });
    els.spanTree.appendChild(fragment);
  }

  renderSelectedSpan(tree.byId.get(state.selectedSpanId), tree.byId);
}

function renderSelectedSpan(span, byId) {
  if (!span) {
    els.selectedSpanTitle.textContent = "Span Info";
    els.selectedSpanKind.textContent = "--";
    els.selectedSpanStatus.textContent = "--";
    els.selectedSpanLatency.textContent = "--";
    els.selectedSpanStart.textContent = "--";
    els.selectedSpanParent.textContent = "--";
    els.selectedSpanAttributes.innerHTML = "";
    els.selectedSpanEvents.innerHTML = "";
    els.selectedSpanRaw.textContent = "";
    return;
  }

  els.selectedSpanTitle.textContent = span.name;
  els.selectedSpanKind.textContent = span.spanKind;
  els.selectedSpanStatus.textContent = span.statusCode;
  els.selectedSpanStatus.className = span.statusCode === "ERROR" ? "status-text-error" : "status-text-ok";
  els.selectedSpanLatency.textContent = fmtDuration(span.latencyMs);
  els.selectedSpanStart.textContent = fmtDate(span.startTime);
  els.selectedSpanParent.textContent =
    span.parentId && byId?.has(span.parentId) ? byId.get(span.parentId).name : "Root";
  els.selectedSpanAttributes.innerHTML = renderAttributesView(span.attributes || {});
  els.selectedSpanEvents.innerHTML = renderEventsView(span.events || []);
  els.selectedSpanRaw.textContent = JSON.stringify(span, null, 2);
}

function setActiveTab(tab) {
  state.ui.activeTab = tab;
  for (const button of els.detailTabs) {
    button.classList.toggle("active", button.dataset.tab === tab);
  }
  for (const panel of els.detailPanels) {
    panel.classList.toggle("active", panel.id === `tab-${tab}`);
  }
}

async function loadProjects() {
  setConnectionStatus("Loading projects", "loading");
  state.projects = await apiGet("/projects");
  renderSidebarCounts();
  renderProjectSummary();
  renderProjectsGrid();
  setConnectionStatus(`Connected to ${apiBaseHost()}`, "live");
}

async function openProject(project) {
  state.selectedProject = project;
  state.selectedTrace = null;
  state.selectedSpanId = null;
  state.collapsedSpans = new Set();
  showView("project");
  setConnectionStatus(`Loading ${project.name}`, "loading");
  state.traces = await apiGet(`/projects/${encodeURIComponent(project.name)}/traces`);
  renderProjectView();
  setConnectionStatus(`${project.name} loaded`, "live");
}

async function openTrace(traceId) {
  showView("trace");
  setConnectionStatus(`Loading trace ${traceId.slice(0, 8)}...`, "loading");
  state.selectedTrace = await apiGet(`/traces/${encodeURIComponent(traceId)}`);
  state.selectedSpanId = null;
  state.collapsedSpans = new Set();
  renderTraceView();
  setConnectionStatus(`Trace ${traceId.slice(0, 8)} loaded`, "live");
}

async function refreshCurrentView() {
  try {
    await loadProjects();
    if (state.selectedProject) {
      const refreshedProject = state.projects.find((item) => item.name === state.selectedProject.name);
      if (refreshedProject) {
        await openProject(refreshedProject);
      }
    }
    if (state.selectedTrace) {
      await openTrace(state.selectedTrace.traceId);
    }
  } catch (error) {
    console.error(error);
    setConnectionStatus("Connection failed", "error");
    if (state.ui.view === "projects") {
      els.projectsGrid.innerHTML = `<div class="empty-state">${error.message}</div>`;
    }
  }
}

els.endpointForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const next = els.endpointInput.value.trim().replace(/\/$/, "");
  if (!next) return;
  state.apiBase = next;
  localStorage.setItem("anvesha.apiBase", next);
  await refreshCurrentView();
});

els.refreshButton.addEventListener("click", refreshCurrentView);
els.backToProjects.addEventListener("click", () => showView("projects"));
els.backToProject.addEventListener("click", () => showView("project"));

els.globalSearch.addEventListener("input", (event) => {
  const value = event.target.value;
  state.filters.global = value;
  if (state.ui.view === "projects") {
    state.filters.project = value;
    renderProjectsGrid();
  } else if (state.ui.view === "project") {
    state.filters.trace = value;
    renderProjectView();
  } else {
    state.filters.span = value;
    renderTraceView();
  }
});

els.traceSearch.addEventListener("input", (event) => {
  state.filters.trace = event.target.value;
  renderProjectView();
});

els.spanSearch.addEventListener("input", (event) => {
  state.filters.span = event.target.value;
  renderTraceView();
});

for (const button of els.detailTabs) {
  button.addEventListener("click", () => setActiveTab(button.dataset.tab));
}

els.endpointInput.value = state.apiBase;
setActiveTab("attributes");
showView("projects");
refreshCurrentView();
