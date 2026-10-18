const STORAGE_KEY = "nexus.ui.v1";
const API_BASE = window.NEXUS_API_BASE || "/api";
const SUPABASE_URL = window.NEXUS_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.NEXUS_SUPABASE_ANON_KEY || "";
const supabaseClient = window.supabase && SUPABASE_URL && SUPABASE_ANON_KEY
  ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;
const initialData = {
  messages: [{ role: "assistant", text: "Hey, I’m Nexus. I can help you keep your health and productivity in sync. What’s on your mind?", time: Date.now() }],
  workouts: [], meals: [], sleep: [], tasks: [], habits: [], reflections: [],
  hiddenThreadIds: [],
  threadTitles: {},
};
let data = loadData();
let currentView = "chat";
let historyFilters = { domain: "all", range: "all", search: "" };
let healthTab = "workouts";
let productivityTab = "tasks";
let toastTimer;
let session = null;
let currentThreadId = null;
let threads = [];
let openThreadMenuId = null;
let backendLogs = { health: [], productivity: [] };
let authMode = "signin";

function setAuthStatus(message, isError = false) {
  const status = document.querySelector("#auth-status");
  if (!status) return;
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function updateAuthScreen() {
  const gate = document.querySelector("#auth-gate");
  const shell = document.querySelector(".app-shell");
  gate?.classList.toggle("is-hidden", Boolean(session));
  shell?.classList.toggle("is-hidden", !session);
}

function updateAuthMode() {
  const signup = authMode === "signup";
  document.querySelector("#auth-kicker").textContent = signup ? "CREATE YOUR ACCOUNT" : "WELCOME BACK";
  document.querySelector("#auth-title").textContent = signup ? "Start with Nexus." : "Your day, connected.";
  document.querySelector("#auth-copy").textContent = signup ? "Create your account to keep your personal assistant in sync." : "Sign in to continue to your personal chief of staff.";
  document.querySelector("#auth-submit").innerHTML = signup ? "Sign up <span>↗</span>" : "Sign in <span>↗</span>";
  document.querySelector("#auth-toggle").textContent = signup ? "Already have an account? Sign in" : "Need an account? Sign up";
  document.querySelector("#auth-password").autocomplete = signup ? "new-password" : "current-password";
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  if (!supabaseClient) {
    setAuthStatus("Add your Supabase URL and anon key in config.js first.", true);
    return;
  }

  const email = document.querySelector("#auth-email").value.trim();
  const password = document.querySelector("#auth-password").value;
  const submit = document.querySelector("#auth-submit");
  submit.disabled = true;
  setAuthStatus(authMode === "signup" ? "Creating your account..." : "Signing you in...");

  const result = authMode === "signup"
    ? await supabaseClient.auth.signUp({ email, password })
    : await supabaseClient.auth.signInWithPassword({ email, password });

  submit.disabled = false;
  if (result.error) {
    setAuthStatus(result.error.message, true);
    return;
  }

  if (authMode === "signup" && !result.data.session) {
    setAuthStatus("Check your email to confirm your account, then sign in.");
    return;
  }

  setAuthStatus("");
}

async function signInWithGoogle() {
  if (!supabaseClient) {
    setAuthStatus("Add your Supabase URL and anon key in config.js first.", true);
    return;
  }
  setAuthStatus("Opening Google sign in...");
  const { error } = await supabaseClient.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
  if (error) setAuthStatus(error.message, true);
}

async function signOut() {
  if (!supabaseClient) return;
  const { error } = await supabaseClient.auth.signOut();
  if (error) toast(error.message);
}

async function boot() {
  document.querySelector("#auth-form").addEventListener("submit", handleAuthSubmit);
  document.querySelector("#auth-google").addEventListener("click", signInWithGoogle);
  document.querySelector("#logout-button").addEventListener("click", signOut);
  document.querySelector("#auth-toggle").addEventListener("click", () => {
    authMode = authMode === "signin" ? "signup" : "signin";
    updateAuthMode();
    setAuthStatus("");
  });
  updateAuthMode();

  if (!supabaseClient) {
    updateAuthScreen();
    setAuthStatus("Add your Supabase URL and anon key in config.js first.", true);
    return;
  }

  const { data } = await supabaseClient.auth.getSession();
  session = data.session;
  updateAuthScreen();
  if (session) {
    render();
    loadThreads().catch(() => {});
    loadBackendLogs().catch(error => toast(error.message));
  }

  supabaseClient.auth.onAuthStateChange((_event, nextSession) => {
    session = nextSession;
    currentThreadId = null;
    updateAuthScreen();
    if (session) {
      render();
      loadThreads().catch(() => {});
      loadBackendLogs().catch(error => toast(error.message));
    }
  });
}

async function authenticatedFetch(path, options = {}) {
  if (!supabaseClient) throw new Error("Supabase client is not configured");
  const { data } = await supabaseClient.auth.getSession();
  const accessToken = data.session?.access_token;
  if (!accessToken) throw new Error("No authenticated session");

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

async function loadThreads() {
  if (!session) return;
  const response = await authenticatedFetch("/threads");
  if (!response.ok) throw new Error(`Thread request failed (${response.status})`);
  const payload = await response.json();
  threads = payload.threads || [];
  renderRecentChats();
  if (currentView === "history") render();
}

function normalizeBackendLog(item, index) {
  const sourceType = item.source_type || item.sourceType || "memory";
  const sourceId = item.source_id ?? item.sourceId ?? index;
  const labels = {
    workouts: "Workout",
    meals: "Meal",
    sleep_logs: "Sleep",
    tasks: "Task",
    habits: "Habit",
    reflections: "Reflection",
  };
  let parsed = null;
  if (sourceType === "tasks" && typeof item.content === "string") {
    try { parsed = JSON.parse(item.content); } catch {}
  }
  const rawTaskContent = sourceType === "tasks" && typeof item.content === "string" ? item.content : "";
  const plainTaskTitle = rawTaskContent.match(/^Task:\s*(.*?)(?:\.\s*(?:Description|Status|Priority|Due date):|$)/i)?.[1]?.trim();
  const plainTaskStatus = rawTaskContent.match(/Status:\s*([^.]+)/i)?.[1]?.trim().toLowerCase();
  return {
    id: `backend-${sourceType}-${sourceId}`,
    title: parsed?.title || plainTaskTitle || labels[sourceType] || "Saved entry",
    detail: parsed?.description || item.description || item.notes || item.content || "Saved by Nexus",
    status: parsed?.status || item.status || plainTaskStatus || "",
    due: parsed?.due_date || item.due_date || "",
    createdAt: item.created_at || item.createdAt || new Date().toISOString(),
    sourceType,
  };
}

function mergeBackendRecords(existing, incoming) {
  const records = new Map(existing.map(item => [String(item.id), item]));
  incoming.forEach(item => records.set(String(item.id), item));
  return [...records.values()];
}

async function loadBackendLogs() {
  if (!session) return;
  const [healthResponse, productivityResponse] = await Promise.all([
    authenticatedFetch("/logs?domain=health&query=recent%20activities&limit=20"),
    authenticatedFetch("/logs?domain=productivity&query=recent%20activities&limit=20"),
  ]);
  if (!healthResponse.ok || !productivityResponse.ok) {
    throw new Error("Backend logs could not be loaded");
  }

  const healthPayload = await healthResponse.json();
  const productivityPayload = await productivityResponse.json();
  const healthLogs = (healthPayload.logs || []).map(normalizeBackendLog);
  const productivityLogs = (productivityPayload.logs || []).map(normalizeBackendLog);

  backendLogs = { health: healthLogs, productivity: productivityLogs };
  data.workouts = mergeBackendRecords(data.workouts, healthLogs.filter(item => item.sourceType === "workouts"));
  data.meals = mergeBackendRecords(data.meals, healthLogs.filter(item => item.sourceType === "meals"));
  data.sleep = mergeBackendRecords(data.sleep, healthLogs.filter(item => item.sourceType === "sleep_logs"));
  data.tasks = mergeBackendRecords(data.tasks, productivityLogs.filter(item => item.sourceType === "tasks"));
  data.habits = mergeBackendRecords(data.habits, productivityLogs.filter(item => item.sourceType === "habits"));
  data.reflections = mergeBackendRecords(data.reflections, productivityLogs.filter(item => item.sourceType === "reflections"));
  saveData();
  render();
}

async function openThread(threadId) {
  const response = await authenticatedFetch(`/threads/${encodeURIComponent(threadId)}/messages`);
  if (!response.ok) throw new Error(`Message request failed (${response.status})`);
  const payload = await response.json();
  currentThreadId = payload.thread_id;
  openThreadMenuId = null;
  data.messages = (payload.messages || []).map(message => ({
    role: message.role === "human" ? "user" : message.role === "ai" ? "assistant" : message.role,
    text: message.content,
    time: Date.now(),
    timeLabel: timeNow(),
  }));
  saveData();
  setView("chat");
  renderRecentChats();
}

function visibleThreads() {
  const hiddenThreadIds = new Set(data.hiddenThreadIds || []);
  return threads.filter(thread => !hiddenThreadIds.has(String(thread.id)));
}

function getThreadTitle(thread) {
  return thread.title || data.threadTitles?.[String(thread.id)] || "Untitled conversation";
}

function renderRecentChats() {
  const list = document.querySelector("#recent-chats");
  if (!list) return;

  const recentThreads = visibleThreads().slice(0, 8);
  list.innerHTML = recentThreads.length
    ? recentThreads.map(thread => {
        const threadId = String(thread.id);
        const isActive = threadId === String(currentThreadId);
        const menuIsOpen = threadId === openThreadMenuId;
        const title = getThreadTitle(thread);
        return `<div class="recent-chat-item ${isActive ? "active" : ""}">
          <button class="recent-chat-open" type="button" data-sidebar-thread-id="${esc(threadId)}" title="${esc(title)}"><span>◷</span><strong>${esc(title)}</strong></button>
          <button class="thread-more-button" type="button" data-thread-menu="${esc(threadId)}" aria-label="Chat options">•••</button>
          ${menuIsOpen ? `<div class="thread-menu"><button type="button" data-hide-thread="${esc(threadId)}">Delete chat</button></div>` : ""}
        </div>`;
      }).join("")
    : `<p class="recent-chat-empty">Your recent chats will appear here.</p>`;

  list.querySelectorAll("[data-sidebar-thread-id]").forEach(button => {
    button.addEventListener("click", () => openThread(button.dataset.sidebarThreadId).catch(error => toast(error.message)));
  });
  list.querySelectorAll("[data-thread-menu]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation();
      openThreadMenuId = button.dataset.threadMenu;
      renderRecentChats();
    });
  });
  list.querySelectorAll("[data-hide-thread]").forEach(button => {
    button.addEventListener("click", () => hideThreadFromSidebar(button.dataset.hideThread));
  });
}

function hideThreadFromSidebar(threadId) {
  data.hiddenThreadIds = [...new Set([...(data.hiddenThreadIds || []), String(threadId)])];
  openThreadMenuId = null;

  if (String(currentThreadId) === String(threadId)) {
    currentThreadId = null;
    data.messages = structuredClone(initialData.messages);
    setView("chat");
  }

  saveData();
  renderRecentChats();
  if (currentView === "history") render();
  toast("Chat removed from this browser.");
}

function loadData() {
  try { return { ...structuredClone(initialData), ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") }; }
  catch { return structuredClone(initialData); }
}
function saveData() { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); }
function esc(value = "") { return String(value).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" })[c]); }
function fmtDate(value, options = { month:"short", day:"numeric" }) { return new Intl.DateTimeFormat(undefined, options).format(new Date(value)); }
function timeNow() { return new Intl.DateTimeFormat(undefined, { hour:"numeric", minute:"2-digit" }).format(new Date()); }
function id() { return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`; }
function toast(message) { const el = document.querySelector("#toast"); el.textContent = message; el.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 2500); }
function setView(view) {
  currentView = view;
  document.querySelectorAll(".nav-link").forEach(button => button.classList.toggle("active", button.dataset.view === view));
  document.querySelector("#current-section").textContent = view.toUpperCase();
  render();
  document.querySelector("#sidebar").classList.remove("open");
  document.querySelector(".mobile-backdrop")?.classList.remove("open");
}
function header(eyebrow, title, subtitle, action = "") {
  return `<div class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${subtitle}</p></div>${action ? `<div class="page-actions">${action}</div>` : ""}</div>`;
}
function addButton(label, type, icon = "+") { return `<button class="button button-dark" data-add="${type}">${label}<span>${icon}</span></button>`; }
function addMenuButton(label, domain) { return `<button class="button button-dark" data-add-menu="${domain}">${label}<span>+</span></button>`; }
function emptyState(icon, title, detail) { return `<div class="empty-state"><div class="empty-icon">${icon}</div><strong>${title}</strong><span>${detail}</span></div>`; }
function sorted(items) { return [...items].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt)); }

function render() {
  const root = document.querySelector("#view-host");
  root.innerHTML = currentView === "chat" ? renderChat() : currentView === "health" ? renderHealth() : currentView === "productivity" ? renderProductivity() : renderHistory();
  bindViewEvents();
  if (currentView === "chat") requestAnimationFrame(scrollChatToLatest);
}

function scrollChatToLatest() {
  const messages = document.querySelector("#chat-messages");
  if (messages) messages.scrollTop = messages.scrollHeight;
}

function renderAssistantMarkdown(text) {
  if (!window.marked || !window.DOMPurify) return esc(text);
  const html = window.marked.parse(String(text), { breaks: true });
  return window.DOMPurify.sanitize(html);
}

function renderChat() {
  const suggestions = ["How have I been sleeping lately?", "What should I focus on today?", "I worked out for 30 minutes", "Show how my health and work are going"];
  const messages = data.messages.map(message => `<article class="message ${message.role}">${message.role === "assistant" && message.meta ? `<div class="message-meta">✦ ${esc(message.meta)}</div>` : ""}<div class="message-bubble">${message.role === "assistant" ? renderAssistantMarkdown(message.text) : esc(message.text)}</div><span class="message-time">${esc(message.timeLabel || timeNow())}</span></article>`).join("");
  return `${header("YOUR PERSONAL CHIEF OF STAFF", `A little more <span class="heading-accent">in sync.</span>`, "One place for your health, your work, and everything between.")}
    <div class="chat-layout"><section class="chat-panel"><div class="chat-topline"><div class="chat-agent"><span class="online-dot"></span>Nexus assistant</div><span class="eyebrow">READY WHEN YOU ARE</span></div><div class="chat-messages" id="chat-messages">${messages}</div><form class="chat-compose" id="chat-form"><div class="compose-box"><textarea id="chat-input" rows="1" placeholder="Tell Nexus what’s on your mind…" aria-label="Message Nexus"></textarea><button class="send-button" aria-label="Send message">↗</button></div><div class="compose-hint"><span>ENTER TO SEND · SHIFT + ENTER FOR NEW LINE</span><span>YOUR DATA STAYS ON THIS DEVICE</span></div></form></section>
    <aside class="suggestion-panel"><span class="eyebrow">A GOOD PLACE TO START</span><h3>Try asking</h3><div class="suggestion-list">${suggestions.map(s => `<button class="suggestion" data-prompt="${esc(s)}">${esc(s)} <span aria-hidden="true">↗</span></button>`).join("")}</div><div class="mini-summary"><p>A quick snapshot</p><div class="domain-dots"><span><i></i>${data.workouts.length + data.meals.length + data.sleep.length} health</span><span><i></i>${data.tasks.length + data.habits.length} productivity</span></div></div></aside></div>`;
}
function renderHealth() {
  const tabs = [["workouts","Workouts"],["meals","Meals"],["sleep","Sleep"]];
  const config = { workouts:["Workout","◉"], meals:["Meal","◌"], sleep:["Sleep","☾"] };
  const all = data[healthTab] || [];
  const latest = sorted(all);
  const stats = [
    ["WORKOUTS THIS MONTH", data.workouts.filter(x => isCurrentMonth(x.createdAt)).length, "Move at your own pace", "↗"],
    ["MEALS LOGGED", data.meals.filter(x => isCurrentMonth(x.createdAt)).length, "Small notes add up", "✳"],
    ["SLEEP ENTRIES", data.sleep.filter(x => isCurrentMonth(x.createdAt)).length, "Rest is part of progress", "☾"],
  ];
  const rows = latest.length ? latest.map(item => `<div class="entry-row"><div class="entry-glyph">${config[healthTab][1]}</div><div class="entry-copy"><div class="entry-title">${esc(item.title)}</div><div class="entry-detail">${esc(item.detail || "Added to your health log")}</div></div><span class="entry-date">${fmtDate(item.createdAt)}</span></div>`).join("") : emptyState(config[healthTab][1], `No ${healthTab} logged yet`, "Add your first entry to start building a picture.");
  return `${header("HEALTH / YOUR LOG", `Take care of <span class="heading-accent">you.</span>`, "A simple place to keep track of movement, meals, and rest.", addMenuButton("Add health entry", "health"))}
    <div class="stat-grid">${stats.map(([label,value,foot,mark]) => `<article class="stat-card"><span class="stat-mark">${mark}</span><div class="stat-label">${label}</div><div class="stat-value">${value}</div><div class="stat-foot">${foot}</div></article>`).join("")}</div>
    <section class="section-card"><div class="section-card-head"><div class="tabs">${tabs.map(([key,label]) => `<button class="tab-button ${healthTab===key?"active":""}" data-health-tab="${key}">${label}</button>`).join("")}</div><span>${all.length} ${all.length===1?"ENTRY":"ENTRIES"}</span></div><div class="card-body"><div class="entry-list">${rows}</div></div></section>`;
}
function isCurrentMonth(value) { const d = new Date(value), now = new Date(); return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear(); }
function isPendingTask(task) { return task.status !== "completed" && !task.done; }
function renderProductivity() {
  const tabs = [["tasks","Tasks"],["habits","Habits"],["reflections","Reflections"]];
  const all = data[productivityTab] || [];
  let body = "";
  if (productivityTab === "tasks") {
    const pendingTasks = all.filter(isPendingTask);
    body = pendingTasks.length
      ? sorted(pendingTasks).map(task => `<div class="entry-row"><div class="entry-glyph">⌘</div><div class="entry-copy"><div class="entry-title">${esc(task.title)}</div><div class="entry-detail">${esc(task.detail || (task.due ? `Due ${fmtDate(task.due,{month:"short",day:"numeric"})}` : "Pending"))}</div></div><span class="entry-date">${fmtDate(task.createdAt)}</span></div>`).join("")
      : emptyState("⌘","No pending tasks","Your current task list is clear.");
  }
  if (productivityTab === "habits") body = all.length ? sorted(all).map(habit => `<div class="entry-row"><div class="entry-glyph">✳</div><div class="entry-copy"><div class="entry-title">${esc(habit.title)}</div><div class="entry-detail">${esc(habit.detail || "A small practice, repeated")}</div><span class="habit-streak">${esc(habit.frequency || "DAILY").toUpperCase()}</span></div><span class="entry-date">${fmtDate(habit.createdAt)}</span></div>`).join("") : emptyState("✳","No habits yet","Choose one small thing you’d like to make a regular part of your day.");
  if (productivityTab === "reflections") body = all.length ? sorted(all).map(note => `<div class="entry-row"><div class="entry-glyph">✎</div><div class="entry-copy"><div class="reflection-box">${esc(note.detail || note.title)}</div></div><span class="entry-date">${fmtDate(note.createdAt)}</span></div>`).join("") : emptyState("✎","A little space to reflect","Save a thought, a win, or something you want to remember.");
  const taskCount = data.tasks.filter(isPendingTask).length;
  return `${header("PRODUCTIVITY / YOUR FLOW", `Make room for <span class="heading-accent">what matters.</span>`, "Tasks, habits, and reflections to help you find your rhythm.", addMenuButton("Add productivity entry", "productivity"))}
    <div class="stat-grid"><article class="stat-card"><span class="stat-mark">⌘</span><div class="stat-label">OPEN TASKS</div><div class="stat-value">${taskCount}</div><div class="stat-foot">One step at a time</div></article><article class="stat-card"><span class="stat-mark">✳</span><div class="stat-label">ACTIVE HABITS</div><div class="stat-value">${data.habits.length}</div><div class="stat-foot">Consistency over intensity</div></article><article class="stat-card"><span class="stat-mark">✎</span><div class="stat-label">REFLECTIONS</div><div class="stat-value">${data.reflections.length}</div><div class="stat-foot">Your thoughts, kept safe</div></article></div>
    <section class="section-card"><div class="section-card-head"><div class="tabs">${tabs.map(([key,label]) => `<button class="tab-button ${productivityTab===key?"active":""}" data-productivity-tab="${key}">${label}</button>`).join("")}</div><span>${all.length} ${all.length===1?"ITEM":"ITEMS"}</span></div><div class="card-body"><div class="entry-list">${body}</div></div></section>`;
}
function historyRows() {
  const records = [
    ...data.workouts.map(x => ({...x,domain:"health",kind:"Workout",glyph:"◉"})), ...data.meals.map(x => ({...x,domain:"health",kind:"Meal",glyph:"◌"})), ...data.sleep.map(x => ({...x,domain:"health",kind:"Sleep",glyph:"☾"})),
    ...data.tasks.map(x => ({...x,domain:"productivity",kind:"Task",glyph:"⌘"})), ...data.habits.map(x => ({...x,domain:"productivity",kind:"Habit",glyph:"✳"})), ...data.reflections.map(x => ({...x,domain:"productivity",kind:"Reflection",glyph:"✎"})),
  ];
  const cutoff = historyFilters.range === "week" ? Date.now()-7*864e5 : historyFilters.range === "month" ? Date.now()-30*864e5 : 0;
  const query = historyFilters.search.toLowerCase();
  return sorted(records).filter(x => (historyFilters.domain === "all" || x.domain === historyFilters.domain) && new Date(x.createdAt).getTime() >= cutoff && (!query || `${x.title} ${x.detail} ${x.kind}`.toLowerCase().includes(query)));
}
function renderHistory() {
  const records = historyRows();
  const rows = records.length ? records.map(item => `<tr><td><span class="tag ${item.domain}">${item.domain}</span></td><td><span class="history-title">${item.glyph} &nbsp;${esc(item.title)}</span><span class="history-detail">${esc(item.detail || item.kind)}</span></td><td>${fmtDate(item.createdAt,{month:"short",day:"numeric",year:"numeric"})}</td></tr>`).join("") : `<tr><td colspan="3">${emptyState("◷","No matching activity","Try another filter or add a new entry.")}</td></tr>`;
  const visibleThreadItems = visibleThreads();
  const threadRows = visibleThreadItems.length
    ? visibleThreadItems.map(thread => `<button class="thread-row" type="button" data-thread-id="${esc(thread.id)}"><span class="thread-icon">◷</span><span class="thread-copy"><strong>${esc(getThreadTitle(thread))}</strong><small>${thread.updated_at ? fmtDate(thread.updated_at,{month:"short",day:"numeric",year:"numeric"}) : "Conversation"}</small></span><span>↗</span></button>`).join("")
    : emptyState("◷", "No saved conversations yet", "Send a chat message to create your first thread.");
  return `${header("HISTORY / THE THROUGH LINE", `Your days, <span class="heading-accent">in view.</span>`, "A combined timeline of the things you’ve logged and worked on.")}
    <section class="section-card thread-card"><div class="section-card-head"><h2>Conversations</h2><span>${visibleThreadItems.length} ${visibleThreadItems.length === 1 ? "THREAD" : "THREADS"}</span></div><div class="thread-list">${threadRows}</div></section>
    <div class="filters"><input class="search-control" id="history-search" type="search" placeholder="⌕  Search your history…" value="${esc(historyFilters.search)}" aria-label="Search history"><select class="control" id="history-domain" aria-label="Filter by category"><option value="all">All activity</option><option value="health" ${historyFilters.domain==="health"?"selected":""}>Health</option><option value="productivity" ${historyFilters.domain==="productivity"?"selected":""}>Productivity</option></select><select class="control" id="history-range" aria-label="Filter by date"><option value="all">Any time</option><option value="week" ${historyFilters.range==="week"?"selected":""}>Past 7 days</option><option value="month" ${historyFilters.range==="month"?"selected":""}>Past 30 days</option></select></div>
    <section class="section-card"><div class="section-card-head"><h2>Recent activity</h2><span>${records.length} ${records.length===1?"RECORD":"RECORDS"}</span></div><div class="card-body" style="padding:0"><table class="history-table"><thead><tr><th>Area</th><th>Activity</th><th>Date</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
}

function bindViewEvents() {
  document.querySelectorAll("[data-add]").forEach(button => button.addEventListener("click", () => openEntry(button.dataset.add)));
  document.querySelectorAll("[data-add-menu]").forEach(button => button.addEventListener("click", () => openEntryChooser(button.dataset.addMenu)));
  document.querySelectorAll("[data-health-tab]").forEach(button => button.addEventListener("click", () => { healthTab = button.dataset.healthTab; render(); }));
  document.querySelectorAll("[data-productivity-tab]").forEach(button => button.addEventListener("click", () => { productivityTab = button.dataset.productivityTab; render(); }));
  document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));
  document.querySelectorAll("[data-thread-id]").forEach(button => button.addEventListener("click", () => openThread(button.dataset.threadId).catch(error => toast(error.message))));
  document.querySelector("[data-new-chat]")?.addEventListener("click", startNewChat);
  const form = document.querySelector("#chat-form");
  if (form) {
    form.addEventListener("submit", event => {
      event.preventDefault();
      const input = document.querySelector("#chat-input");
      sendMessage(input.value);
    });

    const input = document.querySelector("#chat-input");
    input?.addEventListener("keydown", event => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
  }
  const search = document.querySelector("#history-search");
  if (search) search.addEventListener("input", () => { historyFilters.search = search.value; const pos = search.selectionStart; render(); const next = document.querySelector("#history-search"); next.focus(); next.setSelectionRange(pos,pos); });
  const domain = document.querySelector("#history-domain"); if (domain) domain.addEventListener("change", () => { historyFilters.domain = domain.value; render(); });
  const range = document.querySelector("#history-range"); if (range) range.addEventListener("change", () => { historyFilters.range = range.value; render(); });
}

function startNewChat() {
  currentThreadId = null;
  openThreadMenuId = null;
  data.messages = structuredClone(initialData.messages);
  saveData();
  render();
  renderRecentChats();
  toast("New chat ready.");
}

async function sendMessage(text) {
  const value = text.trim(); if (!value) return;
  data.messages.push({ role:"user", text:value, time:Date.now(), timeLabel:timeNow() });
  saveData(); render();
  const box = document.querySelector("#chat-messages"); box.insertAdjacentHTML("beforeend", `<div class="message assistant" id="typing-indicator"><div class="typing"><span></span><span></span><span></span></div></div>`); box.scrollTop = box.scrollHeight;
  try {
    const answer = await requestAssistantReply(value);
    const resolvedThreadId = answer.threadId || currentThreadId;
    if (resolvedThreadId && !data.threadTitles?.[String(resolvedThreadId)]) {
      data.threadTitles = data.threadTitles || {};
      data.threadTitles[String(resolvedThreadId)] = value.slice(0, 56);
    }
    currentThreadId = resolvedThreadId;
    document.querySelector("#typing-indicator")?.remove();
    data.messages.push({ role:"assistant", text:answer.text, meta:answer.meta, time:Date.now(), timeLabel:timeNow() }); saveData(); render();
    loadThreads().catch(() => {});
    document.querySelector("#chat-messages").scrollTop = document.querySelector("#chat-messages").scrollHeight;
  } catch (error) {
    document.querySelector("#typing-indicator")?.remove();
    data.messages.push({ role:"assistant", text:"I can’t reach the Nexus API yet. Start the FastAPI server, then run the UI server with `node server.js` from this UI folder.", meta:"CONNECTION NEEDED", time:Date.now(), timeLabel:timeNow() }); saveData(); render();
  }
}
async function requestAssistantReply(message) {
  if (!supabaseClient) throw new Error("Supabase client is not configured");
  const { data } = await supabaseClient.auth.getSession();
  const accessToken = data.session?.access_token;
  if (!accessToken) throw new Error("No authenticated session");

  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      message,
      thread_id: currentThreadId,
    }),
  });
  if (!response.ok) throw new Error(`Chat request failed (${response.status})`);
  const payload = await response.json();
  return {
    text: payload.response,
    threadId: payload.thread_id,
    meta: "NEXUS RESPONSE",
  };
}
function localAssistantReply(text) {
  const lower = text.toLowerCase();
  const duration = text.match(/\b(\d+)\s*(minutes?|mins?|hours?|hrs?)\b/i);
  const trackWorkout = /\b(worked out|workout|ran|running|exercise|gym|walked|cycling|yoga)\b/.test(lower);
  if (trackWorkout && duration) {
    const title = /run|running|ran/.test(lower) ? "Run" : /walk/.test(lower) ? "Walk" : /yoga/.test(lower) ? "Yoga" : /cycl/.test(lower) ? "Cycling" : "Workout";
    const amount = `${duration[1]} ${duration[2].replace(/s$/i, "")}`;
    data.workouts.push({ id:id(), title, detail:`${amount} · logged from chat`, createdAt:new Date().toISOString() }); saveData();
    return { text:`Logged: ${title.toLowerCase()} for ${amount}. You can find it in your Health screen.`, meta:"HEALTH NOTE SAVED" };
  }
  if (/\b(sleep|slept|rest)\b/.test(lower)) {
    const hours = text.match(/\b(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b/i);
    if (hours && /slept|sleep for|got/.test(lower)) { data.sleep.push({ id:id(), title:`${hours[1]} hours of sleep`, detail:"Logged from chat", createdAt:new Date().toISOString() }); saveData(); return { text:`I’ve added ${hours[1]} hours of sleep to your Health log.`, meta:"HEALTH NOTE SAVED" }; }
    const total = data.sleep.length; return { text:total ? `You have ${total} sleep ${total===1?"entry":"entries"} saved. Add a few more and I can help you spot a pattern.` : "There aren’t any sleep entries yet. Tell me something like “I slept for 7 hours” and I’ll log it for you.", meta:"HEALTH SNAPSHOT" };
  }
  if (/\b(task|focus|work|productiv|today)\b/.test(lower) && !trackWorkout) {
    const open = data.tasks.filter(t => !t.done);
    if (/what should|show|my tasks|focus/.test(lower)) return { text:open.length ? `You have ${open.length} open ${open.length===1?"task":"tasks"}: ${open.slice(0,3).map(t=>t.title).join(", ")}. Pick the smallest next step and start there.` : "Your task list is clear. Add a task in Productivity, or tell me what you’d like to get done and I’ll help you make a plan.", meta:"PRODUCTIVITY SNAPSHOT" };
    if (/\b(add|create|remind me|need to)\b/.test(lower)) { const title = text.replace(/^(please\s+)?(add|create|remind me to|i need to|need to)\s*/i,"").replace(/[.!?]$/ ,"").trim(); if (title.length > 2) { data.tasks.push({ id:id(), title:title[0].toUpperCase()+title.slice(1), detail:"Added from chat", createdAt:new Date().toISOString(), done:false }); saveData(); return { text:`I’ve added “${title}” to your Productivity tasks.`, meta:"PRODUCTIVITY NOTE SAVED" }; } }
  }
  if (/\b(both|health and productivity|overall|how am i doing)\b/.test(lower)) return { text:`Here’s your current snapshot: ${data.workouts.length} workouts, ${data.meals.length} meals, ${data.sleep.length} sleep entries, and ${data.tasks.filter(t=>!t.done).length} open tasks. Keep logging a little at a time and the picture will get clearer.`, meta:"YOUR NEXUS SNAPSHOT" };
  if (/\b(hello|hi|hey)\b/.test(lower)) return { text:"Hey! I’m here. Tell me what you’d like to log, or ask me about your health and productivity.", meta:"NEXUS" };
  return { text:"I’ve got that. I’m currently in personal storage mode, so I can save workouts, sleep notes, and tasks here in the UI. The connected Nexus assistant will be available when the FastAPI endpoint is linked.", meta:"LOCAL MODE" };
}

const entryConfig = {
  workouts:{ kicker:"HEALTH / MOVEMENT", title:"Log a workout", fields:[["workout_type","Activity","text","e.g. Run, strength training"],["duration_minutes","Duration in minutes","number","e.g. 30"],["calories_burned","Calories burned (optional)","number","e.g. 250"],["workout_date","Workout date","date",""] ,["notes","Notes (optional)","textarea","How did it feel?"]] },
  meals:{ kicker:"HEALTH / NUTRITION", title:"Log a meal", fields:[["meal_type","Meal type","text","e.g. Breakfast, lunch, snack"],["description","What did you eat?","textarea","Describe your meal"],["calories","Calories (optional)","number","e.g. 500"],["meal_date","Meal date","date",""]] },
  sleep:{ kicker:"HEALTH / REST", title:"Log your sleep", fields:[["sleep_date","Sleep date","date",""] ,["sleep_hours","Hours slept","number","e.g. 7.5"],["sleep_quality","Sleep quality","select","Poor|Okay|Good|Excellent"],["notes","Notes (optional)","textarea","How rested do you feel?"]] },
  tasks:{ kicker:"PRODUCTIVITY / TASKS", title:"Add a task", fields:[["title","What needs doing?","text","A clear, small next step"],["description","Description (optional)","textarea","Add a little context"],["status","Status","select","pending|in progress|completed"],["priority","Priority","select","low|medium|high"],["due_date","Due date","date",""]] },
  habits:{ kicker:"PRODUCTIVITY / HABITS", title:"Start a habit", fields:[["name","What would you like to practice?","text","e.g. Take a short walk"],["description","Description (optional)","textarea","Make it easy to begin"],["frequency","How often?","select","Daily|A few times a week|Weekly"],["target_count","Target count","number","e.g. 3"],["current_streak","Current streak","number","e.g. 0"],["longest_streak","Longest streak","number","e.g. 0"],["is_active","Active habit","checkbox",""]] },
  reflections:{ kicker:"PRODUCTIVITY / REFLECTION", title:"Save a reflection", fields:[["content","What’s on your mind?","textarea","A small win, a thought, or something you learned"],["mood","Mood (optional)","select","Calm|Good|Tired|Stressed|Excited"],["reflection_date","Reflection date","date",""]] },
};
let activeEntryType = "";
function openEntryChooser(domain) {
  const choices = domain === "health"
    ? [["workouts", "Workout", "Movement, duration, calories, and notes", "◉"], ["meals", "Meal", "Food, calories, and meal notes", "◌"], ["sleep", "Sleep", "Sleep duration, quality, and notes", "☾"]]
    : [["tasks", "Task", "Title, status, priority, and due date", "⌘"], ["habits", "Habit", "Frequency, targets, and streak details", "✳"], ["reflections", "Reflection", "Thoughts, mood, and reflection date", "✎"]];

  activeEntryType = "";
  document.querySelector("#modal-kicker").textContent = domain === "health" ? "HEALTH / ADD TO YOUR LOG" : "PRODUCTIVITY / ADD TO YOUR FLOW";
  document.querySelector("#modal-title").textContent = domain === "health" ? "What would you like to add?" : "What would you like to add?";
  document.querySelector("#modal-fields").innerHTML = `<div class="entry-choice-list">${choices.map(([type, title, detail, icon]) => `<button class="entry-choice" type="button" data-entry-choice="${type}"><span class="entry-choice-icon">${icon}</span><span><strong>${title}</strong><small>${detail}</small></span><span>↗</span></button>`).join("")}</div>`;
  document.querySelector("#modal-submit").hidden = true;
  document.querySelector("#entry-modal").showModal();
  document.querySelectorAll("[data-entry-choice]").forEach(button => button.addEventListener("click", () => {
    document.querySelector("#entry-modal").close();
    openEntry(button.dataset.entryChoice);
  }));
}

function openEntry(type) {
  activeEntryType = type; const config = entryConfig[type]; if (!config) return;
  document.querySelector("#modal-submit").hidden = false;
  document.querySelector("#modal-kicker").textContent = config.kicker; document.querySelector("#modal-title").textContent = config.title;
  document.querySelector("#modal-fields").innerHTML = config.fields.map(([name,label,kind,placeholder]) => {
    const id = `field-${name}`;
    const required = {
      workouts: ["workout_type", "workout_date"],
      meals: ["meal_type", "meal_date"],
      sleep: ["sleep_date", "sleep_hours"],
      tasks: ["title", "due_date"],
      habits: ["name", "frequency"],
      reflections: ["content", "reflection_date"],
    }[activeEntryType]?.includes(name) ? " required" : "";
    if (kind === "select") return `<label class="form-field"><span class="field-label">${label}</span><select class="form-input" name="${name}" id="${id}"${required}>${placeholder.split("|").map(x=>`<option>${x}</option>`).join("")}</select></label>`;
    if (kind === "textarea") return `<label class="form-field"><span class="field-label">${label}</span><textarea class="form-input" name="${name}" id="${id}" rows="3" placeholder="${placeholder}"${required}></textarea></label>`;
    return `<label class="form-field"><span class="field-label">${label}</span><input class="form-input" name="${name}" id="${id}" type="${kind}" placeholder="${placeholder}"${required} /></label>`;
  }).join("");
  document.querySelector("#entry-modal").showModal();
}
function numberOrNull(value) { return value === "" || value == null ? null : Number(value); }

function buildLogPayload(record) {
  if (activeEntryType === "workouts") return { type:"workout", workout_type:record.workout_type, duration_minutes:numberOrNull(record.duration_minutes), calories_burned:numberOrNull(record.calories_burned), notes:record.notes || null, workout_date:record.workout_date };
  if (activeEntryType === "meals") return { type:"meal", meal_type:record.meal_type, description:record.description || null, calories:numberOrNull(record.calories), meal_date:record.meal_date };
  if (activeEntryType === "sleep") return { type:"sleep", sleep_date:record.sleep_date, sleep_hours:Number(record.sleep_hours), sleep_quality:record.sleep_quality || null, notes:record.notes || null };
  if (activeEntryType === "tasks") return { type:"task", title:record.title, description:record.description || null, status:record.status, priority:record.priority, due_date:record.due_date };
  if (activeEntryType === "habits") return { type:"habit", name:record.name, description:record.description || null, frequency:record.frequency, target_count:Number(record.target_count || 1), current_streak:Number(record.current_streak || 0), longest_streak:Number(record.longest_streak || 0), is_active:record.is_active === "on" };
  return { type:"reflection", content:record.content, mood:record.mood || null, reflection_date:record.reflection_date };
}

async function saveStructuredEntry(record) {
  const response = await authenticatedFetch("/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildLogPayload(record)),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Could not save ${activeEntryType}`);
  }
  return response.json();
}

document.querySelector("#entry-form").addEventListener("submit", async event => {
  if (event.submitter?.value === "cancel") return;
  event.preventDefault(); const form = new FormData(event.currentTarget); const record = Object.fromEntries(form.entries());
  const title = record.title || record.name || record.workout_type || record.meal_type || record.content || record.sleep_date || "New entry";
  const detail = record.detail || record.description || record.notes || record.content || record.duration_minutes || record.sleep_hours || "";
  try {
    await saveStructuredEntry(record);
    const item = { id:id(), title, detail, createdAt:new Date().toISOString(), ...record, done:false };
    data[activeEntryType].push(item); saveData(); document.querySelector("#entry-modal").close(); render();
    loadBackendLogs().catch(() => {});
    toast("Saved to your Nexus account.");
  } catch (error) {
    toast(error.message);
  }
});

document.querySelectorAll(".nav-link").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(undefined,{weekday:"short",month:"short",day:"numeric"}).format(new Date()).toUpperCase();
document.querySelector("#mobile-menu").addEventListener("click", () => { document.querySelector("#sidebar").classList.add("open"); document.querySelector(".mobile-backdrop")?.classList.add("open"); });
const backdrop = document.createElement("div"); backdrop.className = "mobile-backdrop"; backdrop.addEventListener("click", () => { document.querySelector("#sidebar").classList.remove("open"); backdrop.classList.remove("open"); }); document.body.append(backdrop);
document.querySelector("#about-button").addEventListener("click", () => toast("Nexus — your personal chief of staff. Your entries are saved in this browser."));
boot();
