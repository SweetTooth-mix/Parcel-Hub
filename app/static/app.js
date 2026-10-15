const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (cents) => `RM ${(Number(cents || 0) / 100).toFixed(2)}`;
const date = (timestamp) =>
  timestamp
    ? new Intl.DateTimeFormat("ms-MY", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Kuala_Lumpur",
      }).format(new Date(timestamp * 1000))
    : "—";
const shortDate = (timestamp) =>
  timestamp
    ? new Intl.DateTimeFormat("ms-MY", {
        day: "numeric",
        month: "short",
        timeZone: "Asia/Kuala_Lumpur",
      }).format(new Date(timestamp * 1000))
    : "—";
const roleName = (role) =>
  ({ recipient: "Penerima", operator: "Operator PAP", admin: "Pentadbir" })[
    role
  ] || "Tetamu";
const paths = {
  box: "m21 8-9-5-9 5v9l9 5 9-5V8ZM3 8l9 5 9-5M12 13v9M7.5 5.5l9 5",
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  home: "m3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9",
  truck:
    "M3 5h11v12H3zM14 9h4l3 4v4h-7M7 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4M18 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  chevron: "m9 5 7 7-7 7",
  check: "m5 12 4 4L19 6",
  clock: "M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  pin: "M19 10c0 6-7 12-7 12S5 16 5 10a7 7 0 0 1 14 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
  search: "M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  logout: "M9 4H4v16h5M9 12h12m-5-5 5 5-5 5",
  user: "M20 21v-2a6 6 0 0 0-6-6h-4a6 6 0 0 0-6 6v2M16 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M20 21v-2a4 4 0 0 0-3-4M17 3a4 4 0 0 1 0 8",
  lock: "M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4M12 14v3",
  qr: "M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h2v2h-2zM20 14v3M14 20h3M20 20h1",
  scan: "M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5M5 12h14",
  settings:
    "M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1z",
  help: "M9 8a3 3 0 1 1 4 3c-1 .6-1 1-1 3M12 17h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "m6 6 12 12M6 18 18 6",
  plus: "M12 5v14M5 12h14",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  refresh: "M21 7v5h-5M3 17v-5h5M5 6a9 9 0 0 1 15 4M4 14a9 9 0 0 0 15 4",
  chart: "M4 21V3M4 21h17M8 17v-5M13 17V7M18 17v-8",
  wallet: "M3 7V5h16v2M3 7h18v14H3zM17 12h4v5h-4z",
  shield: "M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6zM8 12l3 3 5-6",
  info: "M12 11v6M12 7h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  backspace: "m9 4-7 8 7 8h13V4zM12 9l6 6M12 15l6-6",
  rotate: "M3 10a9 9 0 1 1 3 9M3 4v6h6",
  tool: "M14 6a5 5 0 0 0-6 6L2 18l4 4 6-6a5 5 0 0 0 6-6l-3 3-4-4z",
  receipt: "M5 3h14v19l-3-2-4 2-4-2-3 2zM8 7h8M8 11h8M8 15h5",
  mail: "M3 5h18v14H3zM3 5l9 8 9-8",
  send: "m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13",
  moon: "M20.9 13a9 9 0 0 1-9.9-9.9A9 9 0 1 0 20.9 13Z",
  sun: "M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
};
const icon = (name, cls = "") =>
  `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.box}"/></svg>`;
const button = (label, action, kind = "primary", ico = "", extra = "") =>
  `<button class="button ${kind}" data-action="${action}" ${extra}>${ico ? icon(ico) : ""}${label}</button>`;
const brand = () =>
  '<div class="brand"><img src="/static/favicon.svg" alt=""><span>Parcel<b>Hub</b></span></div>';
function themeToggle() {
  const dark = window.ParcelHubTheme.current === "dark";
  return `<button type="button" class="icon-button theme-toggle" data-action="toggle-theme" aria-label="Mod gelap" aria-pressed="${dark}" title="Tukar ke mod ${dark ? "cerah" : "gelap"}">${icon(dark ? "sun" : "moon")}</button>`;
}
function syncThemeControls() {
  const dark = window.ParcelHubTheme.current === "dark";
  for (const control of $$(".theme-toggle")) {
    control.setAttribute("aria-pressed", String(dark));
    control.title = `Tukar ke mod ${dark ? "cerah" : "gelap"}`;
    control.innerHTML = icon(dark ? "sun" : "moon");
  }
  const select = $("#theme-preference");
  if (select) select.value = window.ParcelHubTheme.preference;
}
window.addEventListener("parcelhub:theme-change", syncThemeControls);
const state = {
  user: null,
  csrf: null,
  demo: false,
  hardware_mode: "simulated",
  telegramEnabled: false,
  telegram: null,
  station: { lockers: [], available: 0, occupied: 0, total: 16 },
  parcels: [],
  notifications: [],
  view: "home",
  tab: "active",
  search: "",
  pickup: null,
  kioskStep: "code",
  payment: null,
  selectedLocker: null,
  routeId: 0,
  poll: null,
  stream: null,
  scanTimer: null,
  recipients: [],
  overview: null,
  users: [],
  payments: [],
};
const labels = {
  READY: "Sedia diambil",
  RESERVED: "Sedang disimpan",
  UNLOCK_PENDING: "Menunggu pintu",
  PICKUP_OPEN: "Pintu terbuka",
  COLLECTED: "Selesai diambil",
  ISSUE: "Perlu bantuan",
  CANCELLED: "Dibatalkan",
};
const statusPill = (p) =>
  `<span class="pill ${p.status === "READY" ? (p.fees?.overdue ? "orange" : "green") : ["ISSUE"].includes(p.status) ? "red" : ["PICKUP_OPEN", "UNLOCK_PENDING", "RESERVED"].includes(p.status) ? "blue" : ""}">${p.status === "READY" && p.fees?.overdue ? "Lewat tempoh" : labels[p.status] || esc(p.status)}</span>`;

async function api(url, method = "GET", data) {
  const response = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: {
      ...(data ? { "Content-Type": "application/json" } : {}),
      ...(state.csrf ? { "X-CSRF-Token": state.csrf } : {}),
    },
    ...(data ? { body: JSON.stringify(data) } : {}),
  });
  let result;
  try {
    result = await response.json();
  } catch {
    result = {};
  }
  if (!response.ok) {
    let message = Array.isArray(result.detail)
      ? result.detail.map((e) => e.msg).join(" · ")
      : result.detail || "Sambungan terganggu. Cuba semula.";
    if (
      response.status === 401 &&
      !url.startsWith("/api/kiosk") &&
      !url.includes("/auth/login")
    ) {
      state.user = null;
      state.csrf = null;
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return result;
}
function toast(message, error = false) {
  const el = document.createElement("div");
  el.className = `toast${error ? " error" : ""}`;
  el.setAttribute("role", error ? "alert" : "status");
  el.innerHTML =
    icon(error ? "info" : "check") + `<span>${esc(message)}</span>`;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), 5000);
}
function stopScan() {
  clearTimeout(state.scanTimer);
  state.stream?.getTracks().forEach((t) => t.stop());
  state.stream = null;
}
function openModal(title, content) {
  stopScan();
  const d = $("#modal");
  d.innerHTML = `<div class="modal-header"><h2 id="modal-title">${esc(title)}</h2><button class="icon-button" data-action="close-modal" aria-label="Tutup">${icon("close")}</button></div><div class="modal-body">${content}</div>`;
  if (!d.open) d.showModal();
}
function closeModal() {
  stopScan();
  $("#modal").close();
}
function formError(form, error) {
  const box = $(".error-message", form);
  if (box) box.textContent = error.message;
  else toast(error.message, true);
}
function go(view) {
  if (location.hash === "#" + view) route();
  else location.hash = view;
}
function field(label, name, type = "text", placeholder = "", extra = "") {
  return `<div class="field"><label for="f-${name}">${label}</label><input id="f-${name}" name="${name}" type="${type}" placeholder="${placeholder}" ${extra}></div>`;
}
function stat(label, value, foot, ico = "box", highlight = false) {
  return `<div class="stat"><span class="stat-icon ${highlight ? "orange" : ""}">${icon(ico)}</span><p class="stat-label">${label}</p><div class="stat-value">${value}</div><div class="stat-foot">${foot}</div></div>`;
}
function pageHead(eyebrow, title, subtitle, actions = "") {
  return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${subtitle}</p></div><div class="head-actions">${actions}</div></div>`;
}
function empty(title, text, ico = "box") {
  return `<div class="empty">${icon(ico)}<h3>${title}</h3><p>${text}</p></div>`;
}

function cabinet({ compact = false, controls = false } = {}) {
  const lockerHtml = (l) =>
    `<div class="locker-box ${esc(l.state)} ${state.selectedLocker === l.id ? "selected" : ""}" data-bay="${l.id}" aria-label="Loker ${l.id}: ${l.state}"><div class="locker-interior">${["occupied", "open"].includes(l.state) ? '<div class="mini-parcel"></div>' : ""}</div><div class="locker-door"><span class="locker-id">${l.id}</span><span class="locker-size">${l.size}</span><i class="locker-light"></i></div></div>`;
  const fallback = Array.from({ length: 16 }, (_, i) => ({
    id: i < 8 ? `A0${i + 1}` : i < 12 ? `B0${i - 7}` : `C0${i - 11}`,
    size: i < 4 ? "S" : i < 8 ? "M" : i < 12 ? "L" : "XL",
    state: [1, 8, 13].includes(i) ? "occupied" : "available",
  }));
  const lockers = state.station.lockers.length
    ? state.station.lockers
    : fallback;
  return `<div class="scene ${compact ? "compact" : ""}" role="img" aria-label="Model tiga dimensi loker ParcelHub dengan 16 petak"><div class="cabinet"><div class="tower tower-a">${lockers
    .filter((l) => l.id[0] === "A")
    .map(lockerHtml)
    .join(
      "",
    )}</div><div class="cabinet-kiosk"><div class="mini-brand">Parcel<b>Hub</b></div><div class="mini-screen">${icon("box")}<span>SELAMAT DATANG<br>Ambil parcel anda</span><em></em></div><div class="mini-scanner"></div><span class="mini-kiosk-label">PAP · 01</span></div><div class="tower tower-b">${lockers
    .filter((l) => l.id[0] === "B")
    .map(lockerHtml)
    .join("")}</div><div class="tower tower-c">${lockers
    .filter((l) => l.id[0] === "C")
    .map(lockerHtml)
    .join(
      "",
    )}</div></div>${controls ? `<div class="scene-caption">PAP-01 / SMART LOCKER</div><div class="scene-controls"><button data-action="camera-front" title="Pandangan hadapan" aria-label="Pandangan hadapan">${icon("grid")}</button><button data-action="camera-angle" title="Pandangan bersudut" aria-label="Pandangan bersudut">${icon("box")}</button><button data-action="camera-orbit" title="Gerakan model" aria-label="Gerakan model">${icon("rotate")}</button></div>` : ""}</div>`;
}
function navLink(view, label, ico, badge = "") {
  return `<button class="nav-link ${state.view === view ? "active" : ""}" data-action="nav" data-view="${view}">${icon(ico)}${label}${badge ? `<span class="nav-badge">${badge}</span>` : ""}</button>`;
}
function shell() {
  const u = state.user;
  const staff = u && u.role !== "recipient";
  const unread = state.notifications.filter((n) => !n.read_at).length;
  const names = {
    home: staff ? "Ringkasan operasi" : "Ringkasan",
    parcels: staff ? "Semua parcel" : "Parcel saya",
    kiosk: "Kiosk pengambilan",
    deposit: "Daftar parcel",
    lockers: "Pengurusan loker",
    payments: "Bayaran",
    notifications: "Notifikasi",
    users: "Pengguna",
    help: "Panduan",
    settings: "Akaun & sistem",
  };
  const mainNav = u
    ? navLink("home", "Ringkasan", staff ? "chart" : "home") +
      navLink("parcels", staff ? "Semua parcel" : "Parcel saya", "box") +
      (staff ? navLink("deposit", "Daftar parcel", "plus") : "") +
      navLink("kiosk", "Kiosk loker", "scan") +
      (staff
        ? navLink("lockers", "Petak loker", "grid") +
          navLink("payments", "Bayaran", "wallet")
        : navLink("notifications", "Notifikasi", "bell", unread))
    : navLink("kiosk", "Kiosk loker", "scan");
  const utility =
    (u?.role === "admin" ? navLink("users", "Pengguna", "users") : "") +
    navLink("help", "Panduan", "help") +
    (u ? navLink("settings", "Akaun & sistem", "settings") : "");
  $("#app").innerHTML =
    `<div class="shell"><div class="mobile-overlay" data-action="close-menu"></div><aside class="sidebar">${brand()}<div class="brand-note">CAMPUS PARCEL SERVICE</div><div class="nav-label">RUANG KERJA</div><nav class="nav-list" aria-label="Menu utama">${mainNav}</nav><div class="nav-label">LAIN-LAIN</div><nav class="nav-list" aria-label="Menu tambahan">${utility}</nav><div class="sidebar-bottom"><div class="campus-card"><strong><span class="status-dot"></span>Stesen PAP-01</strong><p>Pusat Aktiviti Pelajar<br>${state.demo ? "Persekitaran demonstrasi" : "Akses tertakluk waktu kampus"}</p></div><button class="user-chip" data-action="${u ? "account" : "login-screen"}"><span class="avatar">${
      u
        ? esc(
            u.name
              .split(" ")
              .slice(0, 2)
              .map((n) => n[0])
              .join(""),
          )
        : "PH"
    }</span><span class="user-info"><strong>${esc(u?.name || "Selamat datang")}</strong><small>${roleName(u?.role)}</small></span>${icon(u ? "chevron" : "user")}</button></div></aside><div class="shell-body"><header class="topbar"><div class="breadcrumb"><button class="icon-button menu-toggle" data-action="menu" aria-label="Buka menu">${icon("menu")}</button><span>Ruang kerja</span>${icon("chevron")}<b>${names[state.view] || "ParcelHub"}</b></div><div class="topbar-right"><span class="topbar-date">${new Intl.DateTimeFormat("ms-MY", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Asia/Kuala_Lumpur" }).format(new Date())}</span>${state.demo ? '<span class="demo-pill">MOD DEMO</span>' : ""}${themeToggle()}${u ? `<button class="icon-button" data-action="nav" data-view="notifications" aria-label="Notifikasi">${icon("bell")}${unread ? '<i class="notif-dot"></i>' : ""}</button>` : button("Log masuk", "login-screen", "secondary", "user")}</div></header><main class="main-content" id="main" tabindex="-1"><div id="view"></div><footer class="footer"><span>© ${new Date().getFullYear()} ParcelHub. Dibina untuk kehidupan kampus.</span><span><span class="status-dot"></span>${state.hardware_mode === "simulated" ? "Simulasi loker · Data disimpan di server" : "Kawalan peranti · PAP-01"}</span></footer></main></div></div>`;
}
function renderAuth(register = false) {
  state.view = "auth";
  clearInterval(state.poll);
  document.title = "Log masuk · ParcelHub";
  $("#app").innerHTML =
    `<div class="auth-shell"><section class="auth-story">${brand()}<div class="story-copy"><div class="eyebrow">YOUR CAMPUS. YOUR PARCEL.</div><h1>Parcel sampai.<br>Ambil ikut<br><em>masa kau.</em></h1><p>Urus parcel kampus dalam satu tempat. Selamat disimpan, mudah diambil di Pusat Aktiviti Pelajar.</p></div>${cabinet()}<div class="story-footer"><span>PAP-01 / PUSAT AKTIVITI PELAJAR</span><span>16 PETAK · 4 SAIZ</span></div></section><main class="auth-form-side" id="main"><div class="auth-tools"><div class="auth-brand-mobile">${brand()}</div>${themeToggle()}</div><div class="eyebrow">${register ? "MULA DENGAN PARCELHUB" : "SELAMAT KEMBALI"}</div><h2>${register ? "Satu akaun, semua parcel." : "Parcel kau, terurus."}</h2><p>${register ? "Daftar sebagai penerima. Gunakan e-mel yang sama semasa operator mendaftarkan parcel." : "Log masuk untuk semak parcel, dapatkan kod pengambilan dan lihat kemas kini terkini."}</p><form id="auth-form" data-register="${register}"><div class="error-message" role="alert"></div>${register ? field("Nama penuh", "name", "text", "Nama pada kad pelajar", 'required minlength="2" maxlength="80" autocomplete="name"') + field("No. matrik / ID staf", "student_id", "text", "Contoh: CA23019", 'required minlength="3" maxlength="30" pattern="[a-zA-Z0-9-]+"') : ""}${field("Alamat e-mel", "email", "email", "nama@kampus.edu.my", 'required maxlength="160" autocomplete="username"')}${field("Kata laluan", "password", "password", register ? "Sekurang-kurangnya 10 aksara" : "Masukkan kata laluan", `required maxlength="128" ${register ? 'minlength="10"' : ""} autocomplete="${register ? "new-password" : "current-password"}"`)}<button type="submit" class="button primary full">${register ? "Cipta akaun" : "Log masuk"}${icon("arrow")}</button></form><div class="auth-switch">${register ? "Sudah ada akaun?" : "Belum ada akaun?"} <button class="text-button" data-action="auth-switch" data-register="${!register}">${register ? "Log masuk" : "Daftar sekarang"}</button></div>${state.demo ? `<div class="divider">CUBA DEMO TANPA MENDAFTAR</div><div class="demo-accounts"><button class="demo-account" data-action="demo-login" data-role="recipient">${icon("user")}Penerima</button><button class="demo-account" data-action="demo-login" data-role="operator">${icon("truck")}Operator</button><button class="demo-account" data-action="demo-login" data-role="admin">${icon("chart")}Admin</button></div><p class="auth-small-note">${state.telegramEnabled ? "Data contoh. Bayaran simulasi; Telegram menghantar mesej sebenar jika disambung." : "Data contoh. Tiada bayaran atau mesej luaran dihantar."}</p>` : ""}${button("Terus ke kiosk pengambilan", "nav", "quiet", "scan", 'data-view="kiosk"')}</main></div>`;
}
function parcelCard(p) {
  return `<article class="panel parcel-card"><div class="row"><div class="courier-logo">${esc(
    p.courier
      .split(" ")
      .map((w) => w[0])
      .join("")
      .slice(0, 3),
  )}</div>${statusPill(p)}</div><h3>${esc(p.courier)}</h3><div class="tracking mono">${esc(p.tracking)}</div><div class="meta-grid"><div><span>LOKER</span><strong>${esc(p.locker_id)} <small class="muted">/ ${p.size}</small></strong></div><div><span>${p.status === "COLLECTED" ? "DIBAYAR" : "CAJ SEMASA"}</span><strong>${money(p.status === "COLLECTED" ? p.paid_cents : p.fees.due_cents)}</strong></div></div>${p.status === "READY" ? button("Kod pengambilan", "code", "primary full", "qr", `data-id="${p.id}"`) : button("Lihat butiran", "detail", "secondary full", "arrow", `data-id="${p.id}"`)}<span class="deadline">${icon("clock")}${p.status === "COLLECTED" ? `Diambil ${date(p.collected_at)}` : p.fees.deadline ? `${p.fees.overdue ? "Lewat sejak" : "Ambil sebelum"} ${date(p.fees.deadline)}` : "Menunggu pengesahan operator"}</span></article>`;
}
function renderHome() {
  if (state.user.role !== "recipient") return renderOverview();
  const active = state.parcels.filter(
    (p) => !["COLLECTED", "CANCELLED"].includes(p.status),
  );
  const ready = active.find((p) => p.status === "READY");
  $("#view").innerHTML =
    pageHead(
      "RUANG PENERIMA",
      `Hai, ${esc(state.user.name.split(" ")[0])}.`,
      "Semua parcel kampus kau, dalam satu tempat.",
      button("Buka kiosk", "nav", "secondary", "scan", 'data-view="kiosk"'),
    ) +
    `<div class="stats">${stat("Parcel aktif", active.length, "Menunggu pengambilan", "box", true)}${stat("Sedia diambil", active.filter((p) => p.status === "READY").length, '<span class="status-dot"></span> Di stesen PAP-01', "check")}${stat("Baki caj", money(active.reduce((n, p) => n + p.fees.due_cents, 0)), "Caj berdasarkan tempoh simpanan", "wallet")}${stat("Selesai diambil", state.parcels.filter((p) => p.status === "COLLECTED").length, "Rekod pengambilan anda", "receipt")}</div><div class="grid-two"><section class="hero"><div class="hero-copy"><div class="hero-badge"><span class="status-dot"></span> PARCELHUB · PAP-01</div><h2>Jadual padat?<br>Parcel <em>tunggu kau.</em></h2><p>Datang ke PAP, sahkan kod dan ambil parcel. Semudah itu.</p>${button("Cara pengambilan", "help-modal", "dark", "arrow")}</div>${cabinet({ compact: true })}</section><section class="panel pickup-highlight"><div><div class="row"><div class="large-icon">${icon("box")}</div><span class="pill ${ready ? "green" : ""}">${ready ? "Sedia diambil" : "Semua terurus"}</span></div><h3>${ready ? "Ada parcel untuk kau." : "Belum ada parcel baharu."}</h3><p>${ready ? esc(ready.courier) + " · " + esc(ready.size) + " / " + date(ready.deposited_at) : "Notifikasi akan muncul selepas operator menyimpan parcel."}</p></div>${ready ? `<div class="row" style="margin:16px 0"><div><div class="tiny muted">LOKER PENGAMBILAN</div><div class="locker-number">${ready.locker_id}</div></div><div style="text-align:right"><div class="tiny muted">BAKI CAJ</div><strong>${money(ready.fees.due_cents)}</strong></div></div>${button("Dapatkan kod pengambilan", "code", "primary full", "qr", `data-id="${ready.id}"`)}` : `<div class="info-note">${icon("bell")}Kami akan maklumkan dalam aplikasi ini.</div>`}</section></div><div class="section-head"><h2>Parcel terkini <small class="muted">(${active.length})</small></h2>${button("Lihat semua", "nav", "quiet", "arrow", 'data-view="parcels"')}</div><div class="parcel-cards">${active.slice(0, 3).map(parcelCard).join("") || `<div class="panel" style="grid-column:1/-1">${empty("Tiada parcel aktif", "Parcel baharu akan disenaraikan di sini selepas didaftarkan.")}</div>`}</div><div class="info-note">${icon("info")}Caj asas RM0.50–RM1.00. Selepas 24 jam, caj tambahan RM1.00 bagi setiap blok 6 jam yang bermula. Akses loker tertakluk waktu akses kampus.</div>`;
}
function filteredParcels() {
  return state.parcels.filter((p) => {
    const tab = state.tab;
    const matchTab =
      tab === "all" ||
      (tab === "active" && !["COLLECTED", "CANCELLED"].includes(p.status)) ||
      (tab === "history" && ["COLLECTED", "CANCELLED"].includes(p.status)) ||
      (tab === "overdue" && p.fees.overdue);
    const str = [
      p.tracking,
      p.locker_id,
      p.courier,
      p.recipient_name,
      p.student_id,
    ]
      .join(" ")
      .toLowerCase();
    return matchTab && str.includes(state.search.toLowerCase());
  });
}
function parcelTable(items, short = false) {
  return `<div class="table-wrap"><table><thead><tr><th>Parcel / kurier</th><th>Penerima</th><th>Loker</th><th>Status</th><th>Baki caj</th><th></th></tr></thead><tbody>${items.map((p) => `<tr><td><strong class="mono">${esc(p.tracking)}</strong><small>${esc(p.courier)} · ${date(p.deposited_at || p.created_at)}</small></td><td><strong>${esc(p.recipient_name)}</strong><small>${esc(p.student_id)}</small></td><td><strong>${p.locker_id}</strong><small>Saiz ${p.size}</small></td><td>${statusPill(p)}</td><td>${money(["COLLECTED", "CANCELLED"].includes(p.status) ? 0 : p.fees.due_cents)}</td><td>${button("Butiran", "detail", "secondary small", "", `data-id="${p.id}"`)}</td></tr>`).join("")}</tbody></table></div>${items.length ? "" : empty("Tiada rekod sepadan", "Ubah penapis atau carian anda.", "search")}<div class="table-caption">${items.length} rekod${short ? " terkini" : " dipaparkan"} · Waktu Malaysia (MYT)</div>`;
}
function renderParcels() {
  const staff = state.user.role !== "recipient";
  $("#view").innerHTML =
    pageHead(
      staff ? "PENGURUSAN PARCEL" : "RUANG PENERIMA",
      staff ? "Semua parcel." : "Parcel saya.",
      "Semak status, caj dan perjalanan setiap parcel.",
      staff
        ? button(
            "Daftar parcel",
            "nav",
            "primary",
            "plus",
            'data-view="deposit"',
          )
        : "",
    ) +
    `<div class="toolbar"><div class="tabs" role="tablist" aria-label="Penapis parcel">${[
      ["active", "Aktif"],
      ["overdue", "Lewat"],
      ["history", "Sejarah"],
      ["all", "Semua"],
    ]
      .map(
        ([v, l]) =>
          `<button role="tab" aria-selected="${state.tab === v}" class="tab ${state.tab === v ? "active" : ""}" data-action="filter-tab" data-tab="${v}">${l}</button>`,
      )
      .join(
        "",
      )}</div><label class="searchbar">${icon("search")}<input id="parcel-search" value="${esc(state.search)}" placeholder="Cari tracking, loker…" aria-label="Cari parcel"></label></div><div id="parcel-results"></div>`;
  renderParcelResults();
}
function renderParcelResults() {
  const rows = filteredParcels();
  $("#parcel-results").innerHTML =
    state.user.role !== "recipient"
      ? `<section class="panel">${parcelTable(rows)}</section>`
      : `<div class="parcel-cards">${rows.map(parcelCard).join("") || `<div class="panel" style="grid-column:1/-1">${empty("Tiada parcel sepadan", "Semak penapis atau tunggu notifikasi parcel baharu.", "search")}</div>`}</div>`;
}
function renderOverview() {
  const o = state.overview;
  const max = Math.max(
    1,
    ...o.trend.flatMap((d) => [d.deposited, d.collected]),
  );
  $("#view").innerHTML =
    pageHead(
      "PUSAT OPERASI",
      "Setiap parcel, dalam kawalan.",
      "Pantau aktiviti dan kapasiti stesen PAP-01 hari ini.",
      button("Daftar parcel", "nav", "primary", "plus", 'data-view="deposit"'),
    ) +
    `<div class="stats">${stat("Parcel aktif", o.active, "Dalam simpanan & pengambilan", "box", true)}${stat("Loker tersedia", `${state.station.available}<small>/ 16</small>`, "Sedia untuk parcel baharu", "grid")}${stat("Lewat tempoh", o.overdue, "Melebihi tempoh asas 24 jam", "clock")}${stat("Kutipan hari ini", money(o.revenue_today_cents), state.demo ? "Transaksi simulasi hari ini" : "Bayaran disahkan hari ini", "wallet")}</div><div class="grid-two"><section class="panel"><div class="panel-head"><div><h2>Pergerakan parcel</h2><p>Tujuh hari terakhir · rekod sebenar aplikasi</p></div><div class="legend"><span><i></i>Masuk</span><span><i class="light"></i>Diambil</span></div></div><div class="chart" role="img" aria-label="${esc(o.trend.map((d) => `${d.day}: ${d.deposited} masuk, ${d.collected} diambil`).join("; "))}">${o.trend.map((d) => `<div class="chart-col" title="${d.day}: ${d.deposited} masuk, ${d.collected} diambil"><div class="chart-bar" style="height:${Math.max(2, (d.deposited / max) * 100)}%"></div><div class="chart-bar light" style="height:${Math.max(2, (d.collected / max) * 100)}%"></div><span class="chart-day">${d.day}</span></div>`).join("")}</div><div class="row" style="padding:0 25px 25px"><div><div class="tiny muted">DIAMBIL HARI INI</div><strong>${o.collected_today} parcel</strong></div><div style="text-align:right"><div class="tiny muted">PURATA BUKA → TUTUP</div><strong>${o.average_pickup_seconds === null ? "Belum ada ukuran" : o.average_pickup_seconds + " saat"}</strong><p class="tiny">${o.measurement_count} pengambilan diukur${state.hardware_mode === "simulated" ? " · simulasi" : ""}</p></div></div></section><section class="panel"><div class="panel-head"><div><h2>Aktiviti terkini</h2><p>Jejak tindakan sistem dan operator</p></div>${icon("clock")}</div><div class="activity">${o.activity
      .slice(0, 4)
      .map(
        (a) =>
          `<div class="activity-item"><div class="activity-mark">${icon(a.action.includes("PAYMENT") ? "wallet" : a.action.includes("DOOR") ? "lock" : "box")}</div><div><strong>${actionLabel(a.action)}</strong><p>${esc(a.parcel_id || a.detail || "PAP-01")}</p></div><time>${new Date(a.created_at * 1000).toLocaleTimeString("ms-MY", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kuala_Lumpur" })}</time></div>`,
      )
      .join(
        "",
      )}</div></section></div><div class="section-head"><h2>Parcel terkini</h2>${button("Lihat semua", "nav", "quiet", "arrow", 'data-view="parcels"')}</div><section class="panel">${parcelTable(state.parcels.slice(0, 5), true)}</section>`;
}
function actionLabel(action) {
  return (
    {
      LOGIN: "Akaun log masuk",
      DEPOSIT_REQUESTED: "Penyimpanan dimulakan",
      PICKUP_REQUESTED: "Pengambilan dimulakan",
      DOOR_OPENED: "Pintu loker dibuka",
      DOOR_CLOSED: "Pintu ditutup",
      PAYMENT_SETTLED: "Bayaran disahkan",
      PICKUP_CODE_REISSUED: "Kod pengambilan baharu",
      IN_APP_REMINDER: "Peringatan dalam aplikasi",
      DEMO_INITIALIZED: "Data demo disediakan",
      USER_CREATED: "Akaun baharu",
      MAINTENANCE_CHANGED: "Penyelenggaraan dikemas kini",
      MANUAL_RECOVERY: "Insiden diselesaikan",
      DOOR_FAULT: "Masalah pintu",
      AUTO_REMINDER: "Peringatan lewat automatik",
    }[action] || action.replaceAll("_", " ").toLowerCase()
  );
}
function renderDeposit() {
  $("#view").innerHTML =
    pageHead(
      "OPERASI STESEN",
      "Simpan parcel baharu.",
      "Daftar penerima, pilih saiz dan simpan parcel dalam loker.",
    ) +
    `<div class="grid-two"><section class="panel panel-pad"><form id="deposit-form"><div class="error-message" role="alert"></div><div class="form-grid"><div class="field wide"><label for="recipient">Penerima berdaftar</label><select id="recipient" name="recipient_id" required><option value="">Pilih penerima</option>${state.recipients.map((u) => `<option value="${u.id}">${esc(u.name)} · ${esc(u.student_id)}</option>`).join("")}</select><small>Penerima boleh mendaftar akaun sendiri. Admin boleh menambah akaun di menu Pengguna.</small></div>${field("Nombor tracking", "tracking", "text", "Contoh: SPXMY01234567", 'required minlength="4" maxlength="60" pattern="[a-zA-Z0-9-]+"')}<div class="field"><label for="courier">Syarikat kurier</label><select id="courier" name="courier" required>${["SPX Express", "J&T Express", "Ninja Van", "Pos Laju", "DHL eCommerce", "Flash Express", "Lain-lain"].map((v) => `<option>${v}</option>`).join("")}</select></div><div class="field"><label for="size">Saiz parcel</label><select id="size" name="size">${["S", "M", "L", "XL"].map((s) => `<option value="${s}">${s} · ${s === "S" || s === "M" ? "RM0.50" : "RM1.00"}</option>`).join("")}</select></div><div class="field"><label for="locker">Petak loker</label><select id="locker" name="locker_id"></select></div></div><div class="info-note">${icon("lock")}Parcel hanya berstatus “Sedia diambil” selepas pintu ditutup dan penyimpanan disahkan.</div><div class="form-actions"><button class="button primary" type="submit">Buka loker & simpan${icon("arrow")}</button></div></form></section><div class="stack"><section class="panel station-panel"><div class="station-top"><div><strong>PAP-01</strong><small>${state.station.available} petak tersedia</small></div><span class="pill green"><span class="status-dot"></span>Sistem tersedia</span></div>${cabinet({ controls: true })}</section></div></div>`;
  updateDepositLockers();
}
function updateDepositLockers() {
  const size = $("#size")?.value;
  const lockers = state.station.lockers.filter(
    (l) => l.size === size && l.state === "available",
  );
  const target = $("#locker");
  if (target)
    target.innerHTML = lockers.length
      ? '<option value="">Pilih secara automatik</option>' +
        lockers.map((l) => `<option value="${l.id}">${l.id}</option>`).join("")
      : '<option value="">Tiada petak tersedia</option>';
}
async function depositDialog(pid) {
  const data = await api("/api/parcels/" + pid);
  const p = data.parcel;
  state.selectedLocker = p.locker_id;
  await refreshStation();
  if (state.view === "deposit") renderDeposit();
  openModal(
    "Simpan parcel · " + p.locker_id,
    `<div class="code-panel"><span class="pill blue">${labels[p.status]}</span><div class="big-locker">${p.locker_id}</div><p>Masukkan <strong>${esc(p.tracking)}</strong> ke dalam loker untuk <strong>${esc(p.recipient_name)}</strong>.</p>${state.hardware_mode === "simulated" ? `<div class="info-note warning">${icon("info")}Pintu dalam mod simulasi. Pilih selepas parcel diletakkan dan pintu ditutup.</div>${button("Parcel disimpan, tutup pintu", "deposit-close", "primary full", "check", `data-id="${pid}" data-present="true"`)}${button("Batal — loker masih kosong", "deposit-close", "quiet full", "", `data-id="${pid}" data-present="false"`)}` : `<div class="info-note">${icon("clock")}Menunggu sensor pintu dan pengesahan parcel daripada peranti.</div>${button("Semak status pintu", "deposit-check", "secondary full", "refresh", `data-id="${pid}"`)}`}</div>`,
  );
}
function renderLockers() {
  const admin = state.user.role === "admin";
  $("#view").innerHTML =
    pageHead(
      "STESEN PAP-01",
      "Ruang untuk setiap parcel.",
      "Status petak dikemas kini daripada pangkalan data stesen.",
      button("Muat semula", "refresh", "secondary", "refresh"),
    ) +
    `<div class="stats">${stat("Jumlah petak", 16, "Empat saiz: S, M, L dan XL", "grid")}${stat("Tersedia", state.station.available, "Boleh menerima parcel", "check", true)}${stat("Digunakan", state.station.occupied, "Parcel dalam simpanan", "box")}${stat("Penyelenggaraan", state.station.lockers.filter((l) => l.maintenance).length, "Dikecualikan daripada agihan", "tool")}</div><section class="panel panel-pad"><div class="row" style="margin-bottom:20px"><h2 style="font-size:18px">Pelan petak loker</h2><span class="tiny muted">${admin ? "Klik petak untuk mengurus" : "PAP-01"}</span></div><div class="locker-grid">${state.station.lockers.map((l) => `<button class="locker-tile ${l.state}" data-action="locker-detail" data-id="${l.id}"><div class="row"><strong>${l.id}</strong>${icon(l.maintenance ? "tool" : l.state === "available" ? "box" : "lock")}</div><div class="row"><small>SAIZ ${l.size}</small><small>${{ available: "Kosong", occupied: "Terisi", maintenance: "Selenggara", open: "Terbuka" }[l.state]}</small></div></button>`).join("")}</div><div class="info-note">${icon("info")}Petak yang digunakan atau pintunya masih terbuka tidak boleh ditawarkan kepada parcel baharu.</div></section>`;
}
function renderNotifications() {
  const unread = state.notifications.some((n) => !n.read_at);
  $("#view").innerHTML =
    pageHead(
      "KEMAS KINI",
      "Notifikasi.",
      "Maklumat terkini tentang parcel anda.",
      button(
        "Tetapan Telegram",
        "nav",
        "secondary",
        "send",
        'data-view="settings"',
      ) +
        (unread
          ? button(
              "Tandakan semua dibaca",
              "read-notifications",
              "secondary",
              "check",
            )
          : ""),
    ) +
    `<section class="panel">${state.notifications.length ? state.notifications.map((n) => `<article class="notification ${n.read_at ? "" : "unread"}"><div class="notification-icon">${icon(n.title.includes("selesai") ? "check" : "box")}</div><div><h3>${esc(n.title)}</h3><p>${esc(n.body)}</p><time>${date(n.created_at)}</time></div>${!n.read_at ? '<span class="status-dot orange" style="margin-left:auto;flex-shrink:0"></span>' : ""}</article>`).join("") : empty("Belum ada notifikasi", "Kemas kini parcel akan muncul di sini.", "bell")}</section>`;
}
function renderPayments() {
  const total = state.payments
    .filter((p) => p.status === "paid")
    .reduce((v, p) => v + p.amount_cents, 0);
  $("#view").innerHTML =
    pageHead(
      "REKOD TRANSAKSI",
      "Bayaran parcel.",
      "Setiap bayaran dipadankan dengan satu rujukan parcel.",
    ) +
    `<div class="stats">${stat("Jumlah disahkan", money(total), state.demo ? "Bayaran simulasi" : "Transaksi dalam senarai ini", "wallet", true)}${stat("Menunggu", state.payments.filter((p) => p.status === "pending" && p.expires_at > Date.now() / 1000).length, "Pengesahan belum diterima", "clock")}${stat("Disahkan", state.payments.filter((p) => p.status === "paid").length, "Direkod secara kekal", "receipt")}${stat("Kaedah", state.demo ? "Demo" : "Kaunter", "Integrasi provider melalui webhook", "shield")}</div><section class="panel"><div class="table-wrap"><table><thead><tr><th>Rujukan / parcel</th><th>Penerima</th><th>Jumlah</th><th>Kaedah</th><th>Status</th><th></th></tr></thead><tbody>${state.payments.map((p) => `<tr><td><strong class="mono">${p.id}</strong><small>${esc(p.tracking)} · ${date(p.created_at)}</small></td><td>${esc(p.recipient_name)}</td><td><strong>${money(p.amount_cents)}</strong></td><td>${p.method === "demo" ? "Simulasi" : p.method === "manual" ? "Kaunter" : esc(p.method)}</td><td><span class="pill ${p.status === "paid" ? "green" : ""}">${{ paid: "Disahkan", pending: p.expires_at > Date.now() / 1000 ? "Menunggu" : "Tamat tempoh", expired: "Tamat tempoh", cancelled: "Dibatalkan" }[p.status] || esc(p.status)}</span></td><td>${p.status === "pending" && p.method === "manual" && p.expires_at > Date.now() / 1000 ? button("Sahkan diterima", "confirm-payment", "secondary small", "", `data-id="${p.id}"`) : ""}</td></tr>`).join("")}</tbody></table></div>${state.payments.length ? "" : empty("Belum ada transaksi", "Transaksi muncul selepas penerima memulakan bayaran di kiosk.", "wallet")}</section>`;
}
function renderUsers() {
  $("#view").innerHTML =
    pageHead(
      "PENTADBIRAN",
      "Akaun & peranan.",
      "Penerima hanya melihat parcel sendiri. Operator dan admin mempunyai akses operasi.",
      button("Tambah pengguna", "new-user", "primary", "plus"),
    ) +
    `<section class="panel"><div class="table-wrap"><table><thead><tr><th>Nama</th><th>E-mel</th><th>ID kampus</th><th>Peranan</th><th>Didaftar</th></tr></thead><tbody>${state.users.map((u) => `<tr><td><strong>${esc(u.name)}</strong></td><td>${esc(u.email)}</td><td class="mono">${esc(u.student_id)}</td><td><span class="pill ${u.role === "admin" ? "orange" : u.role === "operator" ? "blue" : "green"}">${roleName(u.role)}</span></td><td>${shortDate(u.created_at)}</td></tr>`).join("")}</tbody></table></div></section><div class="info-note">${icon("shield")}Akaun yang mendaftar sendiri menerima peranan penerima sahaja. Peranan operator dan admin hanya boleh dicipta oleh admin.</div>`;
}
function helpContent() {
  return `<div class="help-list">${[
    [
      "1",
      "Dapatkan kod pengambilan",
      "Log masuk ke portal. Pilih parcel dan tekan “Kod pengambilan”. Kod baharu menggantikan kod sebelumnya.",
    ],
    [
      "2",
      "Pergi ke PAP-01",
      "Masukkan OTP enam digit pada kiosk atau imbas QR. Semak nombor loker dan caj yang dipaparkan.",
    ],
    [
      "3",
      "Selesaikan bayaran",
      "Caj asas RM0.50 untuk S/M atau RM1.00 untuk L/XL. Caj lewat bermula selepas 24 jam.",
    ],
    [
      "4",
      "Ambil dan tutup pintu",
      "Tunggu pintu dibuka, ambil parcel, kemudian tutup pintu. Pengambilan direkod selepas pengesahan.",
    ],
  ]
    .map(
      ([n, t, p]) =>
        `<div class="help-step"><span class="number">${n}</span><div><strong>${t}</strong><p>${p}</p></div></div>`,
    )
    .join("")}</div>`;
}
function renderHelp() {
  $("#view").innerHTML =
    pageHead(
      "PANDUAN PARCELHUB",
      "Dari loker ke tangan kau.",
      "Empat langkah mudah untuk mengambil parcel.",
    ) +
    `<div class="grid-two"><section class="panel panel-pad">${helpContent()}</section><div><div class="about-card"><h3>Kod tidak berfungsi?</h3><p>Kod sah selama 72 jam selepas dijana. Buka portal dan jana kod baharu jika kod tamat tempoh. Kod yang sudah digunakan tidak boleh membuka parcel lain.</p></div><div class="about-card"><h3>Parcel lewat atau pintu bermasalah?</h3><p>Caj lewat ialah RM1.00 bagi setiap blok enam jam yang bermula selepas 24 jam. Untuk masalah pintu atau parcel, hubungi operator di kaunter PAP. Jangan paksa pintu loker.</p></div><div class="about-card"><h3>Waktu pengambilan</h3><p>Loker menyokong pengambilan di luar waktu kaunter, tertakluk kepada akses fizikal kampus dan ketersediaan sistem.</p></div>${state.demo ? '<div class="info-note warning">' + icon("info") + "Dalam demo, bayaran dan sensor disimulasikan. Notifikasi dalam aplikasi berfungsi; WhatsApp/SMS belum disambungkan.</div>" : ""}</div></div>`;
}
function telegramPanel() {
  const t = state.telegram;
  if (!t) return "";
  const description = !t.enabled
    ? "Telegram belum diaktifkan oleh pentadbir. Notifikasi dalam aplikasi masih tersedia."
    : t.connected
      ? `Disambungkan kepada ${esc(t.display_name)}. Makluman parcel dan peringatan akan dihantar ke chat ini.`
      : "Terima makluman parcel sedia diambil, peringatan lewat dan pengambilan selesai dalam chat Telegram peribadi.";
  const badge = t.connected
    ? '<span class="pill green">Disambungkan</span>'
    : `<span class="pill">${t.enabled ? "Belum disambung" : "Belum diaktifkan"}</span>`;
  return `<section class="panel panel-pad telegram-panel"><div class="row"><h3>${icon("send")}Notifikasi Telegram</h3>${badge}</div><p>${description}</p>${t.enabled && !t.ready ? `<div class="info-note warning">${icon("info")}Bot belum tersedia. Notifikasi dalam aplikasi tetap boleh dibaca.</div>` : ""}${t.connected ? `<div class="telegram-delivery"><span>${t.last_sent_at ? `Dihantar ke Telegram: ${date(t.last_sent_at)}` : "Belum ada mesej dihantar"}</span>${t.pending ? `<span>${t.pending} mesej menunggu</span>` : ""}${t.failed ? `<span class="text-orange">${t.failed} mesej gagal dihantar</span>` : ""}</div>` : ""}<div class="head-actions">${t.connected ? button("Hantar mesej ujian", "telegram-test", "secondary", "send", t.ready ? "" : "disabled") + button("Putuskan sambungan", "telegram-disconnect", "quiet", "close") : t.enabled ? button("Sambung Telegram", "telegram-link", "primary", "send", t.ready ? "" : "disabled") : ""}${button("Semak status", "telegram-refresh", "quiet", "refresh")}</div><p class="tiny">Kod OTP/QR kekal dalam portal. Untuk berhenti, putuskan sambungan di sini atau hantar /stop kepada bot.</p></section>`;
}
function renderSettings() {
  $("#view").innerHTML =
    pageHead(
      "AKAUN & SISTEM",
      "Tetapan anda.",
      "Maklumat akaun dan status konfigurasi ParcelHub.",
    ) +
    `<div class="grid-two"><section class="panel panel-pad"><h3>Maklumat akaun</h3><div class="account-detail"><div class="line-row row"><span>Nama</span><strong>${esc(state.user.name)}</strong></div><div class="line-row row"><span>E-mel</span><strong>${esc(state.user.email)}</strong></div><div class="line-row row"><span>ID kampus</span><strong>${esc(state.user.student_id)}</strong></div><div class="line-row row"><span>Peranan</span><strong>${roleName(state.user.role)}</strong></div></div><div class="head-actions">${button("Tukar kata laluan", "password-modal", "secondary", "lock")}${button("Log keluar", "logout", "quiet", "logout")}</div><div class="theme-settings field"><label for="theme-preference">Tema paparan</label><select id="theme-preference" aria-describedby="theme-hint"><option value="system">Ikut peranti</option><option value="light">Cerah</option><option value="dark">Gelap</option></select><small id="theme-hint">Pilihan tema disimpan dalam pelayar ini.</small></div></section><section class="panel panel-pad"><h3>Status aplikasi</h3><div class="account-detail"><div class="line-row row"><span>Persekitaran</span><strong>${state.demo ? "Demonstrasi" : "Operasi"}</strong></div><div class="line-row row"><span>Sensor pintu</span><strong>${state.hardware_mode === "simulated" ? "Simulasi" : "API peranti"}</strong></div><div class="line-row row"><span>Notifikasi</span><strong>${state.telegram?.connected && state.telegramEnabled ? "Aplikasi + Telegram" : "Dalam aplikasi"}</strong></div><div class="line-row row"><span>Bayaran</span><strong>${state.demo ? "Simulasi" : "Kaunter / adapter webhook"}</strong></div><div class="line-row row"><span>Storan</span><strong>SQLite · server</strong></div></div>${state.user.role === "admin" ? `<a class="button secondary" href="/api/admin/export.csv">${icon("download")}Eksport rekod CSV</a>` : ""}</section></div>`;
  $("#view").insertAdjacentHTML("beforeend", telegramPanel());
  syncThemeControls();
}
function renderKiosk() {
  $("#view").innerHTML =
    pageHead(
      "KIOSK PENGAMBILAN",
      "Parcel kau dah menunggu.",
      "Masukkan kod, selesaikan bayaran dan ambil parcel.",
      button("Cara penggunaan", "help-modal", "secondary", "help"),
    ) +
    `<div class="kiosk-grid"><section class="panel station-panel"><div class="station-top"><div><strong>Pusat Aktiviti Pelajar</strong><small>Stesen PAP-01 · 16 petak loker</small></div><span class="pill green"><span class="status-dot"></span><span data-station-available>${state.station.available} tersedia</span></span></div><div id="kiosk-scene">${cabinet({ controls: true })}</div><div class="station-bottom"><div class="legend"><span><i></i>Kosong</span><span class="taken"><i></i>Terisi</span><span class="offline"><i></i>Selenggara</span></div><small>${state.hardware_mode === "simulated" ? "MODEL SIMULASI" : "STATUS PERANTI"}</small></div></section><section class="panel kiosk-card" id="kiosk-card"></section></div>${state.demo ? `<div class="kiosk-demo"><strong>DATA DEMO · Kod awal untuk parcel contoh. Jika sudah digunakan atau dijana semula, ambil kod terkini daripada portal penerima.</strong><div class="demo-codes"><button data-action="sample-otp" data-code="482910">482910 · Pengambilan biasa</button><button data-action="sample-otp" data-code="591028">591028 · Parcel lewat</button></div></div>` : ""}`;
  renderKioskStep();
}
function kioskProgress(index) {
  return `<div class="kiosk-step">${[0, 1, 2, 3].map((i) => `<div class="step-line ${i <= index ? "active" : ""}"></div>`).join("")}</div><div class="step-label">LANGKAH ${index + 1} / 4 · ${["SAHKAN KOD", "SEMAK & BAYAR", "AMBIL PARCEL", "SELESAI"][index]}</div>`;
}
function renderKioskStep() {
  const el = $("#kiosk-card");
  if (!el) return;
  const p = state.pickup?.parcel;
  if (state.kioskStep === "code")
    el.innerHTML =
      kioskProgress(0) +
      `<h2>Masukkan kod kau.</h2><p>Gunakan OTP enam digit daripada portal ParcelHub.</p><form id="otp-form"><div class="error-message" role="alert"></div><label class="sr-only" for="otp" style="position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)">Kod OTP enam digit</label><input id="otp" class="otp-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" placeholder="— — — — — —" required><div class="keypad">${["1", "2", "3", "4", "5", "6", "7", "8", "9", "padam", "0", "back"].map((k) => `<button type="button" class="${k.length > 1 ? "subtle" : ""}" data-action="keypad" data-key="${k}" ${k === "back" ? 'aria-label="Padam satu digit"' : ""}>${k === "back" ? icon("backspace") : k === "padam" ? "PADAM" : k}</button>`).join("")}</div><button type="submit" class="button primary full">Teruskan${icon("arrow")}</button></form>${button("Imbas kod QR", "qr-scan", "quiet full", "scan")}<div class="kiosk-bottom">${icon("shield")} Kod disahkan oleh server. Maklumat parcel kekal peribadi.</div>`;
  else if (state.kioskStep === "payment") {
    const q = state.pickup.quote;
    const paid = state.payment?.status === "paid";
    const due = paid ? 0 : Math.max(0, q.total_cents - p.paid_cents);
    el.innerHTML =
      kioskProgress(1) +
      `<h2>${due ? "Semak caj pengambilan." : "Bayaran selesai."}</h2><p>Parcel ${esc(p.courier)} berada di loker <strong>${p.locker_id}</strong>.</p><div class="kiosk-price"><small>RM</small>${(due / 100).toFixed(2)}</div><p class="tiny">${due ? "Baki perlu dibayar" : "Tiada baki bayaran"}</p><div class="kiosk-summary"><div class="line-row row"><span>Nombor tracking</span><strong class="mono">${esc(p.tracking)}</strong></div><div class="line-row row"><span>Caj asas · saiz ${p.size}</span><strong>${money(q.base_cents)}</strong></div><div class="line-row row"><span>Caj lewat · ${q.late_blocks} blok × RM1.00</span><strong>${money(q.late_cents)}</strong></div><div class="line-row row"><span>Bayaran diterima</span><strong class="text-green">${money(p.paid_cents)}</strong></div></div>${due ? button(state.demo ? "Simulasi bayaran " + money(due) : "Dapatkan rujukan bayaran", "kiosk-pay", "primary full", "wallet") : button("Buka loker " + p.locker_id, "kiosk-unlock", "primary full", "lock")}${state.payment?.status === "pending" && !state.demo ? `<div class="info-note">${icon("info")}Bayar di kaunter dan sebut rujukan <strong>${state.payment.id}</strong>.</div>${button("Semak pengesahan bayaran", "kiosk-check-payment", "secondary full", "refresh")}` : ""}<div class="info-note ${state.demo ? "warning" : ""}">${icon("info")}${state.demo ? "Bayaran demo sahaja. Tiada wang sebenar dicaj." : "Bayaran perlu disahkan operator atau penyedia bayaran."}</div>${button("Batal pengambilan", "kiosk-reset", "quiet full")}<div class="kiosk-bottom">Sesi dan harga sah selama 10 minit selepas kod disahkan.</div>`;
  } else if (state.kioskStep === "open") {
    const open = p.status === "PICKUP_OPEN";
    el.innerHTML =
      kioskProgress(2) +
      `<h2>${open ? "Pintu dah terbuka." : "Membuka pintu…"}</h2><p>${open ? "Ambil parcel kau dari loker di bawah." : "Menunggu pengesahan daripada peranti loker."}</p><div class="big-locker">${p.locker_id}</div><p style="text-align:center">${esc(p.courier)} · ${esc(p.tracking)}</p>${open && state.hardware_mode === "simulated" ? `<div class="info-note warning">${icon("info")}Simulasi sensor: sahkan pengambilan dan penutupan pintu.</div><div style="margin-top:25px">${button("Parcel diambil, tutup pintu", "kiosk-close", "primary full", "check", 'data-present="false"')}${button("Tutup pintu, parcel masih di dalam", "kiosk-close", "quiet full", "", 'data-present="true"')}</div>` : `<div class="info-note">${icon("clock")}Status akan dikemas kini secara automatik selepas sensor mengesahkan pintu ditutup.</div>${button("Semak status", "kiosk-poll", "secondary full", "refresh")}`}<div class="kiosk-bottom">${button("Pintu bermasalah?", "kiosk-help", "quiet", "help")}</div>`;
  } else if (state.kioskStep === "done")
    el.innerHTML =
      kioskProgress(3) +
      `<div class="kiosk-success"><div class="success-check">${icon("check")}</div><h2>Parcel dah di tangan.</h2><p>Pengambilan selesai. Terima kasih kerana menutup pintu.</p><div class="kiosk-summary"><div class="line-row row"><span>Parcel</span><strong class="mono">${esc(p.tracking)}</strong></div><div class="line-row row"><span>Loker</span><strong>${p.locker_id}</strong></div><div class="line-row row"><span>Jumlah dibayar</span><strong>${money(p.paid_cents)}</strong></div><div class="line-row row"><span>Selesai</span><strong>${date(p.collected_at)}</strong></div></div>${button("Selesai", "kiosk-reset", "primary full", "check")}</div><div class="kiosk-bottom">Rekod pengambilan tersedia di portal penerima.</div>`;
}
async function refreshStation() {
  state.station = await api("/api/station");
}
async function refreshKioskScene() {
  await refreshStation();
  const s = $("#kiosk-scene");
  if (!s) return;
  for (const locker of state.station.lockers) {
    const bay = s.querySelector(`[data-bay="${locker.id}"]`);
    if (!bay) continue;
    bay.classList.remove(
      "available",
      "occupied",
      "open",
      "maintenance",
      "selected",
    );
    bay.classList.add(locker.state);
    bay.classList.toggle("selected", state.selectedLocker === locker.id);
    bay.setAttribute("aria-label", `Loker ${locker.id}: ${locker.state}`);
    const inside = bay.querySelector(".locker-interior");
    if (
      ["occupied", "open"].includes(locker.state) &&
      !inside.querySelector(".mini-parcel")
    )
      inside.innerHTML = '<div class="mini-parcel"></div>';
    if (locker.state === "available") inside.innerHTML = "";
  }
  const available = $("[data-station-available]");
  if (available) available.textContent = state.station.available + " tersedia";
}
function resetKiosk() {
  clearInterval(state.poll);
  state.pickup = null;
  state.payment = null;
  state.kioskStep = "code";
  state.selectedLocker = null;
  renderKiosk();
}
async function verifyCode(code) {
  const result = await api("/api/kiosk/verify", "POST", { code });
  state.pickup = result;
  state.payment = null;
  state.kioskStep = "payment";
  state.selectedLocker = result.parcel.locker_id;
  renderKioskStep();
  await refreshKioskScene();
}
async function pollKiosk() {
  if (!state.pickup || state.kioskStep !== "open") return;
  const data = await api("/api/kiosk/status", "POST", {
    token: state.pickup.token,
  });
  state.pickup.parcel = data.parcel;
  if (data.parcel.status === "COLLECTED") {
    state.kioskStep = "done";
    clearInterval(state.poll);
  } else if (data.parcel.status === "ISSUE") {
    clearInterval(state.poll);
    toast("Masalah pintu dikesan. Sila hubungi operator PAP.", true);
  } else if (data.parcel.status === "READY") {
    toast(
      "Pintu ditutup dengan parcel masih di dalam. Sahkan kod untuk mencuba lagi.",
    );
    resetKiosk();
    return;
  }
  renderKioskStep();
  await refreshKioskScene();
}
async function showCode(pid) {
  const r = await api(`/api/parcels/${pid}/code`, "POST", {});
  const p = state.parcels.find((p) => p.id === pid);
  const src =
    "data:image/svg+xml;charset=utf-8," + encodeURIComponent(r.qr_svg);
  openModal(
    "Kod pengambilan",
    `<div class="code-panel"><span class="pill green">PAP-01 · Loker ${esc(p?.locker_id)}</span><div class="qr-box"><img src="${esc(src)}" width="173" height="173" alt="Kod QR pengambilan parcel"></div><div class="code-display">${esc(r.otp)}</div><p style="margin-top:9px">Sah sehingga ${date(r.expires_at)}</p><div class="info-note">${icon("shield")}Kod ini peribadi. Kod sebelumnya telah dibatalkan.</div>${button("Gunakan di kiosk", "use-code", "primary full", "scan", `data-code="${r.otp}"`)}<p class="tiny" style="margin-top:10px">QR boleh diimbas pada kiosk yang mempunyai kamera.</p></div>`,
  );
}
async function showDetail(pid) {
  const { parcel: p, command } = await api("/api/parcels/" + pid);
  const staff = state.user.role !== "recipient";
  openModal(
    "Butiran parcel",
    `${statusPill(p)}<h3 style="margin:16px 0 5px">${esc(p.courier)}</h3><p class="mono tiny">${esc(p.tracking)}</p><div class="account-detail">${staff ? `<div class="line-row row"><span>Penerima</span><strong>${esc(p.recipient_name)}</strong></div>` : ""}<div class="line-row row"><span>Loker / saiz</span><strong>${p.locker_id} / ${p.size}</strong></div><div class="line-row row"><span>Disimpan</span><strong>${date(p.deposited_at)}</strong></div><div class="line-row row"><span>Tarikh akhir asas</span><strong>${date(p.fees.deadline)}</strong></div><div class="line-row row"><span>Jumlah dibayar</span><strong>${money(p.paid_cents)}</strong></div>${p.status === "COLLECTED" ? `<div class="line-row row"><span>Diambil</span><strong>${date(p.collected_at)}</strong></div>` : `<div class="line-row row"><span>Baki caj semasa</span><strong>${money(p.fees.due_cents)}</strong></div>`}</div>${p.problem ? `<div class="info-note warning">${icon("info")}${esc(p.problem)}</div>` : ""}<div class="head-actions">${p.status === "READY" ? (staff ? button("Hantar peringatan", "remind", "secondary", "bell", `data-id="${pid}"`) : button("Kod pengambilan", "code", "primary", "qr", `data-id="${pid}"`)) : ""}${p.status === "RESERVED" && staff ? button("Teruskan penyimpanan", "resume-deposit", "primary", "box", `data-id="${pid}"`) : ""}${state.user.role === "admin" && ["RESERVED", "UNLOCK_PENDING", "PICKUP_OPEN", "ISSUE"].includes(p.status) ? button("Pemulihan manual", "resolve-modal", "secondary", "tool", `data-id="${pid}"`) : ""}</div>${command ? `<p class="tiny muted" style="margin-top:16px">Status pintu: ${esc(command.state)}</p>` : ""}`,
  );
}
function newUserModal() {
  openModal(
    "Tambah pengguna",
    `<form id="user-form"><div class="error-message" role="alert"></div><div class="form-grid">${field("Nama penuh", "name", "text", "", 'required minlength="2" maxlength="80"')}${field("ID kampus", "student_id", "text", "", 'required minlength="3" maxlength="30" pattern="[a-zA-Z0-9-]+"')}${field("Alamat e-mel", "email", "email", "", 'required maxlength="160"')}${field("Kata laluan awal", "password", "password", "10 aksara atau lebih", 'required minlength="10" maxlength="128" autocomplete="new-password"')}<div class="field wide"><label for="user-role">Peranan</label><select id="user-role" name="role"><option value="recipient">Penerima</option><option value="operator">Operator PAP</option><option value="admin">Admin</option></select></div></div><div class="info-note">${icon("info")}Berikan kata laluan awal secara peribadi dan minta pengguna menukarnya selepas log masuk.</div><div class="form-actions"><button class="button primary" type="submit">Cipta akaun${icon("plus")}</button></div></form>`,
  );
}
function showResolve(pid) {
  openModal(
    "Pemulihan manual",
    `<form id="resolve-form" data-id="${pid}"><div class="error-message" role="alert"></div><div class="info-note warning">${icon("info")}Gunakan selepas operator memeriksa loker secara fizikal. Semua perubahan direkod dalam log audit.</div><div class="field" style="margin:18px 0"><label for="outcome">Hasil pemeriksaan</label><select name="outcome" id="outcome"><option value="restore">Parcel masih di dalam — sedia diambil semula</option><option value="collected">Penerima telah mengambil parcel</option><option value="cancel">Batalkan deposit / rekod tanpa bayaran</option></select></div><div class="field"><label for="reason">Catatan pemeriksaan</label><textarea name="reason" id="reason" required minlength="10" maxlength="300" placeholder="Nyatakan masalah, tindakan dan hasil pemeriksaan"></textarea></div><label class="checkbox"><input type="checkbox" name="door_closed_confirmed" required>Saya telah mengesahkan pintu ditutup dan keadaan parcel sepadan dengan pilihan di atas.</label><div class="form-actions"><button class="button primary" type="submit">Simpan hasil pemeriksaan</button></div></form>`,
  );
}
function lockerDetail(id) {
  const l = state.station.lockers.find((l) => l.id === id);
  const active = state.parcels.find(
    (p) => p.locker_id === id && !["COLLECTED", "CANCELLED"].includes(p.status),
  );
  openModal(
    "Petak loker " + id,
    `<div class="row"><h3>Saiz ${l.size}</h3><span class="pill ${l.state === "available" ? "green" : ""}">${{ available: "Kosong", occupied: "Terisi", open: "Pintu terbuka", maintenance: "Penyelenggaraan" }[l.state]}</span></div><div class="account-detail"><div class="line-row row"><span>Caj asas</span><strong>${money(l.fee_cents)}</strong></div><div class="line-row row"><span>Lokasi</span><strong>PAP-01</strong></div></div>${active ? button("Lihat parcel dalam loker", "detail", "primary full", "box", `data-id="${active.id}"`) : ""}${state.user.role === "admin" && !active && !l.door_open ? `<form id="maintenance-form" data-id="${id}" data-enabled="${!l.maintenance}"><div class="error-message" role="alert"></div><div class="field"><label for="maint-reason">Catatan ${l.maintenance ? "pengaktifan" : "penyelenggaraan"}</label><textarea id="maint-reason" name="reason" minlength="5" maxlength="300" required placeholder="Nyatakan sebab perubahan"></textarea></div><div class="form-actions"><button class="button ${l.maintenance ? "primary" : "secondary"}" type="submit">${l.maintenance ? "Aktifkan semula" : "Tandakan penyelenggaraan"}</button></div></form>` : ""}`,
  );
}
function scannerModal() {
  openModal(
    "Imbas kod QR",
    `<video id="scanner-video" class="video-scanner" playsinline muted hidden></video><div id="scanner-message" class="info-note">${icon("scan")}Benarkan kamera untuk mengimbas QR ParcelHub. Jika kamera tidak disokong, gunakan OTP atau tampal kandungan QR.</div>${button("Hidupkan kamera", "start-camera", "primary full", "scan", 'style="margin-top:15px"')}<div class="divider">ATAU TAMPAL KANDUNGAN QR</div><form id="qr-form"><div class="error-message" role="alert"></div><div class="field"><label for="qr-value">Kod daripada pengimbas</label><input id="qr-value" name="code" required maxlength="100" placeholder="PARCELHUB:…" autocomplete="off"></div><div class="form-actions"><button class="button secondary" type="submit">Sahkan kod</button></div></form>`,
  );
}
async function startCamera() {
  if (!("BarcodeDetector" in window) || !navigator.mediaDevices?.getUserMedia) {
    $("#scanner-message").textContent =
      "Pelayar ini tidak menyokong pengimbasan kamera. Gunakan OTP enam digit atau tampal kandungan QR di bawah.";
    return;
  }
  try {
    const detector = new BarcodeDetector({ formats: ["qr_code"] });
    state.stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
    });
    const video = $("#scanner-video");
    video.hidden = false;
    video.srcObject = state.stream;
    await video.play();
    $("#scanner-message").textContent = "Halakan kamera pada kod QR ParcelHub.";
    const scan = async () => {
      if (!state.stream || !$("#modal").open) return;
      try {
        const codes = await detector.detect(video);
        const code = codes.find((c) => c.rawValue.startsWith("PARCELHUB:"));
        if (code) {
          stopScan();
          await verifyCode(code.rawValue);
          closeModal();
          return;
        }
      } catch (error) {
        $("#scanner-message").textContent = error.message;
      }
      state.scanTimer = setTimeout(scan, 250);
    };
    scan();
  } catch {
    stopScan();
    $("#scanner-message").textContent =
      "Kamera tidak tersedia atau kebenaran ditolak. Gunakan OTP atau tampal kandungan QR.";
  }
}
async function route() {
  const routeId = ++state.routeId;
  clearInterval(state.poll);
  stopScan();
  const view = location.hash.slice(1) || "home";
  if (!state.user && !["kiosk", "help"].includes(view)) {
    renderAuth(view === "register");
    return;
  }
  const allowed =
    state.user?.role === "admin"
      ? [
          "home",
          "parcels",
          "kiosk",
          "deposit",
          "lockers",
          "payments",
          "notifications",
          "users",
          "help",
          "settings",
        ]
      : state.user?.role === "operator"
        ? [
            "home",
            "parcels",
            "kiosk",
            "deposit",
            "lockers",
            "payments",
            "notifications",
            "help",
            "settings",
          ]
        : state.user
          ? ["home", "parcels", "kiosk", "notifications", "help", "settings"]
          : ["kiosk", "help"];
  state.view = allowed.includes(view) ? view : allowed[0];
  document.title =
    ({
      home: "Ringkasan",
      parcels: "Parcel",
      kiosk: "Kiosk",
      deposit: "Daftar parcel",
      lockers: "Loker",
      notifications: "Notifikasi",
      users: "Pengguna",
      payments: "Bayaran",
      settings: "Tetapan",
      help: "Panduan",
    }[state.view] || "ParcelHub") + " · ParcelHub";
  shell();
  $("#view").innerHTML =
    '<div class="empty"><span class="loader"></span><p>Memuatkan rekod…</p></div>';
  try {
    const jobs = [refreshStation()];
    if (state.user) {
      jobs.push(
        api("/api/notifications").then((d) => {
          if (routeId === state.routeId) state.notifications = d.notifications;
        }),
      );
      if (["home", "parcels", "lockers"].includes(state.view))
        jobs.push(
          api("/api/parcels").then((d) => {
            if (routeId === state.routeId) state.parcels = d.parcels;
          }),
        );
      if (state.view === "home" && state.user.role !== "recipient")
        jobs.push(
          api("/api/admin/overview").then((d) => {
            if (routeId === state.routeId) state.overview = d;
          }),
        );
      if (state.view === "deposit")
        jobs.push(
          api("/api/recipients").then((d) => {
            if (routeId === state.routeId) state.recipients = d.users;
          }),
        );
      if (state.view === "payments")
        jobs.push(
          api("/api/admin/payments").then((d) => {
            if (routeId === state.routeId) state.payments = d.payments;
          }),
        );
      if (state.view === "settings")
        jobs.push(
          api("/api/telegram").then((d) => {
            if (routeId === state.routeId) state.telegram = d;
          }),
        );
      if (state.view === "users")
        jobs.push(
          api("/api/admin/users").then((d) => {
            if (routeId === state.routeId) state.users = d.users;
          }),
        );
    }
    await Promise.all(jobs);
    if (routeId !== state.routeId) return;
    shell();
    ({
      home: renderHome,
      parcels: renderParcels,
      kiosk: renderKiosk,
      deposit: renderDeposit,
      lockers: renderLockers,
      notifications: renderNotifications,
      users: renderUsers,
      payments: renderPayments,
      help: renderHelp,
      settings: renderSettings,
    })[state.view]();
    if (
      state.view === "kiosk" &&
      state.kioskStep === "open" &&
      state.hardware_mode === "device"
    )
      startPolling();
  } catch (error) {
    if (routeId !== state.routeId) return;
    if (!state.user && !["kiosk", "help"].includes(state.view)) {
      renderAuth();
      toast(error.message, true);
      return;
    }
    $("#view").innerHTML =
      `<section class="panel">${empty("Rekod belum dapat dimuatkan", esc(error.message), "info")}<div style="text-align:center;padding:0 20px 30px">${button("Cuba semula", "refresh", "primary", "refresh")}</div></section>`;
  }
}
function startPolling() {
  clearInterval(state.poll);
  state.poll = setInterval(
    () =>
      pollKiosk().catch((e) => {
        clearInterval(state.poll);
        toast(e.message, true);
      }),
    2500,
  );
}
async function signedIn(result) {
  state.user = result.user;
  state.csrf = result.csrf;
  state.tab = "active";
  state.search = "";
  history.replaceState(null, "", "#home");
  await route();
}
async function handleAction(el) {
  const action = el.dataset.action;
  switch (action) {
    case "telegram-link": {
      const link = await api("/api/telegram/link", "POST", {});
      openModal(
        "Sambung Telegram",
        `<div class="telegram-link"><p>Buka bot melalui pautan ini, kemudian tekan <strong>Start</strong> dalam Telegram. Kembali ke sini untuk semak sambungan.</p><a class="button primary full" href="${esc(link.url)}" target="_blank" rel="noopener noreferrer">${icon("send")}Buka Telegram</a><p class="tiny">Pautan peribadi ini sah sehingga ${date(link.expires_at)}. Jangan kongsikannya.</p>${state.demo ? '<div class="info-note warning">Telegram menghantar mesej sebenar walaupun parcel dalam mod demo. Gunakan akaun ParcelHub sendiri.</div>' : ""}${button("Saya sudah tekan Start", "telegram-refresh", "secondary full", "refresh")}</div>`,
      );
      break;
    }
    case "telegram-refresh":
      state.telegram = await api("/api/telegram");
      if (state.telegram.connected) closeModal();
      if (state.view === "settings") renderSettings();
      if ($("#modal").open)
        toast(
          "Belum disambung. Tekan Start dalam Telegram, kemudian semak lagi.",
        );
      break;
    case "telegram-disconnect":
      openModal(
        "Putuskan Telegram?",
        `<p>Notifikasi dalam aplikasi kekal tersedia. Mesej Telegram yang sedang dihantar mungkin masih sampai.</p><div class="form-actions">${button("Batal", "close-modal", "secondary")}${button("Putuskan sambungan", "telegram-confirm-disconnect", "danger")}</div>`,
      );
      break;
    case "telegram-confirm-disconnect":
      await api("/api/telegram/disconnect", "POST", {});
      state.telegram = await api("/api/telegram");
      closeModal();
      renderSettings();
      toast("Telegram diputuskan.");
      break;
    case "telegram-test":
      await api("/api/telegram/test", "POST", {});
      state.telegram = await api("/api/telegram");
      renderSettings();
      toast(
        "Mesej ujian dalam giliran penghantaran. Semak Telegram sebentar lagi.",
      );
      break;
    case "toggle-theme":
      window.ParcelHubTheme.set(
        window.ParcelHubTheme.current === "dark" ? "light" : "dark",
      );
      break;
    case "nav":
      closeModal();
      go(el.dataset.view);
      break;
    case "menu":
      $(".sidebar").classList.add("is-open");
      $(".mobile-overlay").classList.add("visible");
      break;
    case "close-menu":
      $(".sidebar").classList.remove("is-open");
      $(".mobile-overlay").classList.remove("visible");
      break;
    case "close-modal":
      closeModal();
      break;
    case "refresh":
      if (!state.initialized) await boot();
      else await route();
      break;
    case "login-screen":
      history.replaceState(null, "", "#login");
      renderAuth();
      break;
    case "auth-switch":
      renderAuth(el.dataset.register === "true");
      break;
    case "demo-login":
      await signedIn(
        await api("/api/auth/demo", "POST", { role: el.dataset.role }),
      );
      break;
    case "logout":
      await api("/api/auth/logout", "POST", {});
      state.user = null;
      state.csrf = null;
      state.parcels = [];
      state.notifications = [];
      state.pickup = null;
      state.kioskStep = "code";
      state.payment = null;
      history.replaceState(null, "", "#login");
      closeModal();
      renderAuth();
      break;
    case "account":
      openModal(
        "Akaun anda",
        `<h3>${esc(state.user.name)}</h3><p style="margin:8px 0 23px">${esc(state.user.email)} · ${roleName(state.user.role)}</p><div class="head-actions">${button("Tetapan akaun", "nav", "secondary", "settings", 'data-view="settings"')}${button("Log keluar", "logout", "quiet", "logout")}</div>`,
      );
      break;
    case "password-modal":
      openModal(
        "Tukar kata laluan",
        `<form id="password-form"><div class="error-message" role="alert"></div><div class="stack">${field("Kata laluan semasa", "current_password", "password", "", 'required autocomplete="current-password" maxlength="128"')}${field("Kata laluan baharu", "new_password", "password", "Sekurang-kurangnya 10 aksara", 'required autocomplete="new-password" minlength="10" maxlength="128"')}</div><div class="info-note">${icon("shield")}Semua sesi akan ditamatkan selepas kata laluan ditukar.</div><div class="form-actions"><button class="button primary" type="submit">Tukar kata laluan</button></div></form>`,
      );
      break;
    case "filter-tab":
      state.tab = el.dataset.tab;
      renderParcels();
      break;
    case "code":
      await showCode(el.dataset.id);
      break;
    case "use-code": {
      const code = el.dataset.code;
      closeModal();
      history.replaceState(null, "", "#kiosk");
      await route();
      await verifyCode(code);
      break;
    }
    case "detail":
      await showDetail(el.dataset.id);
      break;
    case "help-modal":
      openModal("Cara pengambilan", helpContent());
      break;
    case "read-notifications":
      await api("/api/notifications/read", "POST", {});
      await route();
      toast("Semua notifikasi ditandakan dibaca.");
      break;
    case "new-user":
      newUserModal();
      break;
    case "locker-detail":
      lockerDetail(el.dataset.id);
      break;
    case "resume-deposit":
      await depositDialog(el.dataset.id);
      break;
    case "deposit-close": {
      await api(`/api/parcels/${el.dataset.id}/deposit-close`, "POST", {
        parcel_present: el.dataset.present === "true",
      });
      closeModal();
      state.selectedLocker = null;
      await route();
      toast(
        el.dataset.present === "true"
          ? "Parcel disimpan. Penerima menerima notifikasi dalam aplikasi."
          : "Deposit dibatalkan. Loker tersedia semula.",
      );
      break;
    }
    case "deposit-check": {
      const d = await api("/api/parcels/" + el.dataset.id);
      if (d.parcel.status === "READY") {
        closeModal();
        toast("Penyimpanan disahkan oleh peranti.");
        await route();
      } else if (d.parcel.status === "ISSUE") {
        closeModal();
        await showDetail(el.dataset.id);
      } else toast("Masih menunggu pengesahan peranti.");
      break;
    }
    case "remind":
      await api(`/api/admin/parcels/${el.dataset.id}/remind`, "POST", {});
      toast("Peringatan dihantar dalam aplikasi.");
      break;
    case "resolve-modal":
      showResolve(el.dataset.id);
      break;
    case "confirm-payment": {
      const pay = state.payments.find((p) => p.id === el.dataset.id);
      openModal(
        "Sahkan bayaran kaunter",
        `<p>Pastikan <strong>${money(pay.amount_cents)}</strong> sudah diterima untuk rujukan <strong>${pay.id}</strong>.</p><div class="info-note warning">${icon("info")}Tindakan ini merekod bayaran sebenar dan akan dimasukkan dalam log audit.</div><div class="form-actions">${button("Bayaran telah diterima", "settle-cash", "primary", "check", `data-id="${pay.id}"`)}</div>`,
      );
      break;
    }
    case "settle-cash":
      await api(`/api/admin/payments/${el.dataset.id}/confirm`, "POST", {});
      closeModal();
      await route();
      toast("Bayaran kaunter disahkan.");
      break;
    case "camera-front": {
      const s = el.closest(".scene");
      s.classList.remove("orbit");
      s.classList.add("front");
      break;
    }
    case "camera-angle":
      el.closest(".scene").classList.remove("front", "orbit");
      break;
    case "camera-orbit":
      el.closest(".scene").classList.toggle("orbit");
      break;
    case "keypad": {
      const input = $("#otp");
      const k = el.dataset.key;
      input.value =
        k === "padam"
          ? ""
          : k === "back"
            ? input.value.slice(0, -1)
            : (input.value + k).slice(0, 6);
      break;
    }
    case "sample-otp":
      resetKiosk();
      $("#otp").value = el.dataset.code;
      $("#otp").focus();
      break;
    case "qr-scan":
      scannerModal();
      break;
    case "start-camera":
      await startCamera();
      break;
    case "kiosk-pay": {
      const r = await api("/api/kiosk/payment", "POST", {
        token: state.pickup.token,
      });
      state.payment = r.payment;
      if (r.demo) {
        await api(`/api/kiosk/payment/${r.payment.id}/simulate`, "POST", {
          token: state.pickup.token,
        });
        state.payment.status = "paid";
        const status = await api("/api/kiosk/status", "POST", {
          token: state.pickup.token,
        });
        state.pickup.parcel = status.parcel;
        toast("Bayaran demo disahkan.");
      }
      renderKioskStep();
      break;
    }
    case "kiosk-check-payment": {
      const r = await api("/api/kiosk/status", "POST", {
        token: state.pickup.token,
      });
      state.pickup.parcel = r.parcel;
      if (!r.due_cents) {
        state.payment.status = "paid";
        toast("Bayaran telah disahkan.");
      } else toast("Bayaran masih menunggu pengesahan.");
      renderKioskStep();
      break;
    }
    case "kiosk-unlock": {
      const r = await api("/api/kiosk/unlock", "POST", {
        token: state.pickup.token,
      });
      state.pickup.parcel = r.parcel;
      state.kioskStep = "open";
      renderKioskStep();
      await refreshKioskScene();
      if (state.hardware_mode === "device") startPolling();
      break;
    }
    case "kiosk-close": {
      const present = el.dataset.present === "true";
      const r = await api("/api/kiosk/close", "POST", {
        token: state.pickup.token,
        parcel_present: present,
      });
      state.pickup.parcel = r.parcel;
      if (present) {
        toast("Parcel masih disimpan. Sahkan kod untuk mencuba lagi.");
        resetKiosk();
      } else {
        state.kioskStep = "done";
        renderKioskStep();
      }
      await refreshKioskScene();
      break;
    }
    case "kiosk-reset":
      resetKiosk();
      await refreshKioskScene();
      break;
    case "kiosk-poll":
      await pollKiosk();
      break;
    case "kiosk-help":
      openModal(
        "Bantuan loker",
        `<p>Hubungi operator di kaunter PAP dan berikan nombor loker <strong>${esc(state.pickup?.parcel.locker_id)}</strong>. Jangan paksa pintu.</p><div class="info-note">${icon("info")}Operator boleh memeriksa status dan admin boleh merekod pemulihan manual selepas pemeriksaan fizikal.</div>`,
      );
      break;
  }
}
document.addEventListener("click", async (event) => {
  const el = event.target.closest("[data-action]");
  if (!el || el.disabled) return;
  event.preventDefault();
  if (el.tagName === "BUTTON") el.disabled = true;
  try {
    await handleAction(el);
  } catch (error) {
    toast(error.message, true);
  } finally {
    if (el.isConnected) el.disabled = false;
  }
});
document.addEventListener("submit", async (event) => {
  const form = event.target;
  if (!form.id) return;
  event.preventDefault();
  const submit = $('[type="submit"]', form);
  if (submit?.disabled) return;
  if (submit) submit.disabled = true;
  const errorBox = $(".error-message", form);
  if (errorBox) errorBox.textContent = "";
  const values = Object.fromEntries(new FormData(form));
  try {
    switch (form.id) {
      case "auth-form":
        await signedIn(
          await api(
            form.dataset.register === "true"
              ? "/api/auth/register"
              : "/api/auth/login",
            "POST",
            values,
          ),
        );
        break;
      case "otp-form":
        await verifyCode($("#otp").value);
        break;
      case "qr-form":
        await verifyCode(values.code);
        closeModal();
        break;
      case "deposit-form": {
        values.recipient_id = Number(values.recipient_id);
        if (!values.locker_id) delete values.locker_id;
        const d = await api("/api/parcels", "POST", values);
        await depositDialog(d.parcel.id);
        break;
      }
      case "user-form":
        await api("/api/admin/users", "POST", values);
        closeModal();
        await route();
        toast("Akaun pengguna dicipta.");
        break;
      case "maintenance-form":
        await api(`/api/admin/lockers/${form.dataset.id}`, "PATCH", {
          reason: values.reason,
          enabled: form.dataset.enabled === "true",
        });
        closeModal();
        await route();
        toast("Status penyelenggaraan dikemas kini.");
        break;
      case "resolve-form":
        await api(`/api/admin/parcels/${form.dataset.id}/resolve`, "POST", {
          ...values,
          door_closed_confirmed: values.door_closed_confirmed === "on",
        });
        closeModal();
        await route();
        toast("Pemeriksaan direkod dan status dikemas kini.");
        break;
      case "password-form":
        await api("/api/auth/password", "POST", values);
        state.user = null;
        state.csrf = null;
        state.pickup = null;
        state.kioskStep = "code";
        closeModal();
        history.replaceState(null, "", "#login");
        renderAuth();
        toast("Kata laluan ditukar. Sila log masuk semula.");
        break;
    }
  } catch (error) {
    formError(form, error);
  } finally {
    if (submit?.isConnected) submit.disabled = false;
  }
});
document.addEventListener("input", (event) => {
  if (event.target.id === "parcel-search") {
    state.search = event.target.value;
    renderParcelResults();
  }
  if (event.target.id === "otp")
    event.target.value = event.target.value.replace(/\D/g, "").slice(0, 6);
});
document.addEventListener("change", (event) => {
  if (event.target.id === "size") updateDepositLockers();
  if (event.target.id === "theme-preference")
    window.ParcelHubTheme.set(event.target.value);
});
$("#modal").addEventListener("close", stopScan);
window.addEventListener("hashchange", route);
window.addEventListener("beforeunload", () => {
  stopScan();
  clearInterval(state.poll);
});
async function boot() {
  try {
    const [me, station] = await Promise.all([
      api("/api/me"),
      api("/api/station"),
    ]);
    Object.assign(state, {
      initialized: true,
      user: me.user,
      csrf: me.csrf,
      demo: me.demo,
      hardware_mode: me.hardware_mode,
      telegramEnabled: me.telegram_enabled,
      station,
    });
    await route();
  } catch (error) {
    $("#app").innerHTML =
      `<main class="initial-loader"><h2>ParcelHub belum tersedia.</h2><p>${esc(error.message)}</p>${button("Cuba semula", "refresh", "primary", "refresh")}</main>`;
  }
}
boot();

// Refresh server-backed views without replacing an active form, modal or kiosk session.
setInterval(async () => {
  if (!state.user || !state.initialized || document.hidden || $("#modal").open)
    return;
  if (!["home", "parcels", "lockers", "notifications"].includes(state.view))
    return;
  if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName))
    return;
  const routeId = state.routeId;
  const userId = state.user.id;
  try {
    const responses = await Promise.all([
      api("/api/notifications"),
      api("/api/parcels"),
      api("/api/station"),
      state.view === "home" && state.user.role !== "recipient"
        ? api("/api/admin/overview")
        : Promise.resolve(null),
    ]);
    if (routeId !== state.routeId || state.user?.id !== userId) return;
    const [notifications, parcels, station, overview] = responses;
    const changed =
      JSON.stringify([
        state.notifications,
        state.parcels,
        state.station,
        state.overview,
      ]) !==
      JSON.stringify([
        notifications.notifications,
        parcels.parcels,
        station,
        overview || state.overview,
      ]);
    state.notifications = notifications.notifications;
    state.parcels = parcels.parcels;
    state.station = station;
    if (overview) state.overview = overview;
    if (changed) {
      if (state.view === "home") renderHome();
      if (state.view === "parcels") renderParcelResults();
      if (state.view === "lockers") renderLockers();
      if (state.view === "notifications") renderNotifications();
      const bell = $('.topbar [data-view="notifications"]');
      if (bell)
        bell.innerHTML =
          icon("bell") +
          (state.notifications.some((n) => !n.read_at)
            ? '<i class="notif-dot"></i>'
            : "");
    }
  } catch (error) {
    if (error.status === 401) {
      closeModal();
      renderAuth();
    }
    // A transient outage leaves the last readable snapshot in place; actions still surface errors.
  }
}, 15000);
