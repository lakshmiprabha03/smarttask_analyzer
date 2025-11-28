// ======================================================================
//  Smart Task Analyzer
// ======================================================================


// -----------------------------------------------------
// GLOBAL STATE & ELEMENTS
// -----------------------------------------------------
let tasks = [];

const holidayMode = document.getElementById("holidayMode");
const holidayInput = document.getElementById("customHolidays");

const modal = document.getElementById("taskModal");
const modalBox = document.getElementById("modalBox");
const saveTaskBtn = document.getElementById("saveTaskBtn");
const closeModalBtn = document.getElementById("closeModalBtn");

const taskTemplate = document.getElementById("taskTemplate");
const dropZone = document.getElementById("dropZone");

let modalMode = "create";
let editTaskId = null;


// -----------------------------------------------------
// UTILITIES
// -----------------------------------------------------
const safeJSON = (t) => { try { return JSON.parse(t); } catch { return null; } };

const escape = (s) =>
    !s ? "" : String(s).replace(/[&<>"'`=\/]/g, (m) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
        "/": "&#x2F;",
        "`": "&#96;",
        "=": "&#61;",
    }[m]));

const deps = (v) =>
    !v
        ? []
        : Array.isArray(v)
        ? v.map(Number).filter((n) => !isNaN(n))
        : String(v)
              .split(",")
              .map((x) => Number(x.trim()))
              .filter((n) => !isNaN(n));

const nextId = () => (tasks.length ? Math.max(...tasks.map((t) => t.id)) + 1 : 1);

const normalizeTask = (t, id) => ({
    id,
    title: t.title || "Untitled Task",
    due_date: t.due_date || null,
    estimated_hours: Number(t.estimated_hours) || 1,
    importance: Math.max(1, Math.min(10, Number(t.importance) || 5)),
    dependencies: deps(t.dependencies),
});


// -----------------------------------------------------
// MESSAGE
// -----------------------------------------------------
function toast(msg) {
    const t = document.createElement("div");
    t.textContent = msg;
    Object.assign(t.style, {
        position: "fixed",
        bottom: "20px",
        right: "20px",
        background: "#111",
        color: "#fff",
        padding: "12px 16px",
        borderRadius: "8px",
        zIndex: "9999",
    });
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 1800);
}


// -----------------------------------------------------
// HOLIDAY PAYLOAD
// -----------------------------------------------------
function buildHolidays() {
    const mode = holidayMode.value;

    const indian = [
        "2025-01-14",
        "2025-01-26",
        "2025-08-15",
        "2025-10-24",
        "2025-10-02",
        "2025-12-25",
    ];

    if (mode === "none") return [];
    if (mode === "indian") return indian;

    let custom = [];
    if (mode === "custom" || mode === "both") {
        const raw = holidayInput.value.trim();
        if (raw.length) {
            const parsed = safeJSON(raw);
            if (!Array.isArray(parsed)) {
                alert("Custom holidays must be a JSON array.");
                return null;
            }
            custom = parsed.map(String);
        }
    }

    if (mode === "custom") return custom;
    if (mode === "both") return [...new Set([...indian, ...custom])];

    return [];
}

holidayMode.addEventListener("change", () => {
    holidayInput.style.display =
        holidayMode.value === "custom" || holidayMode.value === "both"
            ? "block"
            : "none";
});
holidayInput.style.display = "none";


// -----------------------------------------------------
// MERGE BULK JSON
// -----------------------------------------------------
function mergeBulk() {
    const txt = document.getElementById("jsonInput").value.trim();
    if (!txt) return true;

    const parsed = safeJSON(txt);
    if (!Array.isArray(parsed)) {
        alert("Bulk JSON must be an array.");
        return false;
    }

    const map = new Map();
    tasks.forEach((t) => map.set(t.id, normalizeTask(t, t.id)));

    let idCounter = nextId();
    parsed.forEach((obj) => {
        const id = Number(obj.id) || idCounter++;
        map.set(id, normalizeTask(obj, id));
    });

    tasks = [...map.values()].sort((a, b) => a.id - b.id);
    renderList();
    return true;
}


// -----------------------------------------------------
// MANUAL TASK FORM
// -----------------------------------------------------
document.getElementById("taskForm").addEventListener("submit", (e) => {
    e.preventDefault();

    const idRaw = document.getElementById("id").value.trim();
    const title = document.getElementById("title").value.trim();
    const due = document.getElementById("due_date").value || null;
    const hours = Number(document.getElementById("estimated_hours").value) || 1;
    const imp = Number(document.getElementById("importance").value) || 5;
    const d = deps(document.getElementById("dependencies").value);

    if (!title) return alert("Title required.");

    const id = idRaw ? Number(idRaw) : nextId();
    tasks.push(
        normalizeTask(
            { title, due_date: due, estimated_hours: hours, importance: imp, dependencies: d },
            id
        )
    );
    renderList();
});


// -----------------------------------------------------
// RENDER TASK LIST
// -----------------------------------------------------
function renderList() {
    const container = document.getElementById("taskList");
    container.innerHTML = "";

    if (!tasks.length) {
        container.innerHTML = "<p>No tasks yet.</p>";
        return;
    }

    tasks.forEach((t) => {
        const row = document.createElement("div");
        row.className = "task-row";

        row.innerHTML = `
            <div style="display:flex; gap:10px; align-items:center;">
                <strong>${t.id}</strong>
                <div>
                    <div>${escape(t.title)}</div>
                    <div style="font-size:12px;color:#ccc;">
                        Due: ${escape(t.due_date || "—")} · Eff: ${t.estimated_hours}h · Imp: ${t.importance}
                    </div>
                </div>
            </div>
            <div class="task-actions">
                <button class="edit-btn" data-id="${t.id}">✏️</button>
                <button class="delete-btn" data-id="${t.id}">🗑️</button>
            </div>
        `;

        container.appendChild(row);
    });

    document.querySelectorAll(".edit-btn").forEach((b) => (b.onclick = () => openEditModal(Number(b.dataset.id))));
    document.querySelectorAll(".delete-btn").forEach((b) => (b.onclick = () => deleteTask(Number(b.dataset.id))));
}


// -----------------------------------------------------
// ANALYZE → BACKEND
// -----------------------------------------------------
document.getElementById("analyzeBtn").addEventListener("click", async () => {
    if (!mergeBulk()) return;
    if (!tasks.length) return alert("Add tasks first.");

    const holidays = buildHolidays();
    if (holidays === null) return;

    const payload = {
        tasks,
        strategy: document.getElementById("strategy").value,
        holidays,
    };

    showLoading(true);

    try {
        const res = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();
        showLoading(false);

        if (!res.ok) return alert("Error: " + JSON.stringify(data));
        renderResults(data.tasks);
    } catch (err) {
        showLoading(false);
        alert("Network error: " + err.message);
    }
});

function showLoading(show) {
    document.getElementById("results").innerHTML = show ? "<p>Analyzing...</p>" : "";
}


// -----------------------------------------------------
// RENDER RESULTS
// -----------------------------------------------------
function renderResults(list) {
    const box = document.getElementById("results");
    box.innerHTML = "<h2>Results</h2>";

    list.forEach((t) => {
        const card = document.createElement("div");
        card.className = "task-card";

        const cls =
            t.score >= 70
                ? "priority-high"
                : t.score >= 40
                ? "priority-medium"
                : "priority-low";

        card.innerHTML = `
            <strong>${escape(t.title)}</strong><br>
            <span class="${cls}">Score: ${t.score}</span><br><br>
            Due: ${escape(t.due_date || "None")}<br>
            Effort: ${t.estimated_hours}h · Importance: ${t.importance}<br><br>
            <small>${escape(t.explanation)}</small>
        `;

        box.appendChild(card);
    });
}


// -----------------------------------------------------
// SUGGEST → (TOP 3)
// -----------------------------------------------------
document.getElementById("suggestBtn").addEventListener("click", async () => {
    if (!mergeBulk()) return;
    if (!tasks.length) return alert("Add tasks first.");

    const holidays = buildHolidays();
    if (holidays === null) return;

    const payload = {
        tasks,
        strategy: document.getElementById("strategy").value,
        holidays,
    };

    const box = document.getElementById("suggestions");
    box.innerHTML = "Loading...";

    try {
        const res = await fetch("http://127.0.0.1:8000/api/tasks/suggest/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) return alert("Error: " + JSON.stringify(data));
        renderSuggestions(data.suggestions);
    } catch (err) {
        alert("Network error: " + err.message);
    }
});


function renderSuggestions(list) {
    const box = document.getElementById("suggestions");
    box.innerHTML = "<h2>Top 3 Suggestions</h2>";

    list.forEach((s) => {
        const card = document.createElement("div");
        card.className = "task-card";

        const cls = s.score >= 70 ? "priority-high" : s.score >= 40 ? "priority-medium" : "priority-low";

        card.innerHTML = `
            <strong>${escape(s.title)}</strong><br>
            <span class="${cls}">Score: ${s.score}</span><br>
            <small>${escape(s.why || "")}</small>
            <div style="margin-top:10px;">
                <button class="fb btn" data-helpful="true" data-id="${s.id}" data-score="${s.score}">👍 Helpful</button>
                <button class="fb btn" style="background:#ff5252" data-helpful="false" data-id="${s.id}" data-score="${s.score}">👎 Not Helpful</button>
            </div>
        `;

        box.appendChild(card);
    });

    document.querySelectorAll(".fb").forEach((btn) => {
        btn.onclick = () =>
            sendFeedback({
                helpful: btn.dataset.helpful === "true",
                task_id: Number(btn.dataset.id),
                score: Number(btn.dataset.score),
            });
    });
}


// -----------------------------------------------------
// FEEDBACK
// -----------------------------------------------------
function sendFeedback(obj) {
    fetch("http://127.0.0.1:8000/api/tasks/feedback/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
    })
        .then((r) => r.json())
        .then(() => toast("Feedback recorded — learning updated"))
        .catch((err) => alert("Feedback error: " + err.message));
}


// -----------------------------------------------------
// DEPENDENCY GRAPH
// -----------------------------------------------------
document.getElementById("visualizeBtn").addEventListener("click", () => {
    if (!tasks.length) return alert("Add tasks first.");
    renderGraph(tasks);
});


function findCycleNodes(list) {
    const graph = {};
    list.forEach((t) => (graph[t.id] = t.dependencies || []));

    const visited = {};
    const stack = [];
    const cycles = new Set();

    function dfs(u) {
        visited[u] = 1;
        stack.push(u);

        for (const v of graph[u]) {
            if (!visited[v]) dfs(v);
            else if (visited[v] === 1) {
                const idx = stack.indexOf(v);
                if (idx >= 0) stack.slice(idx).forEach((n) => cycles.add(n));
            }
        }

        stack.pop();
        visited[u] = 2;
    }

    Object.keys(graph).map(Number).forEach((n) => {
        if (!visited[n]) dfs(n);
    });

    return cycles;
}


function renderGraph(list) {
    const container = document.getElementById("graphContainer");
    container.style.display = "block";

    const nodes = list.map((t) => ({
        id: t.id,
        label: `${t.title}\n(ID:${t.id})`,
        shape: "box",
        color: "#1976D2",
    }));

    const edges = [];
    list.forEach((t) =>
        t.dependencies.forEach((d) =>
            edges.push({ from: d, to: t.id, arrows: "to", color: "#aaa" })
        )
    );

    const cycles = findCycleNodes(list);
    nodes.forEach((n) => {
        if (cycles.has(n.id)) n.color = "#D32F2F";
    });

    new vis.Network(
        container,
        { nodes, edges },
        { layout: { hierarchical: { direction: "UD" }}, physics: false }
    );
}


// -----------------------------------------------------
// EISENHOWER MATRIX
// -----------------------------------------------------
document.getElementById("matrixBtn").addEventListener("click", () => {
    if (!tasks.length) return alert("Add tasks first.");
    renderMatrix(tasks);
});


function renderMatrix(list) {
    const container = document.getElementById("matrixContainer");
    container.style.display = "block";

    const zones = [
        ["doFirst", "Do First (Urgent + Important)"],
        ["schedule", "Schedule (Not Urgent + Important)"],
        ["delegate", "Delegate (Urgent + Not Important)"],
        ["eliminate", "Eliminate (Not Urgent + Not Important)"],
    ];

    zones.forEach(([id, title]) => {
        const box = document.getElementById(id);
        box.innerHTML = `
            <div class="matrix-title"><strong>${title}</strong></div>
            <div class="matrix-content"></div>
        `;
    });

    list.forEach((t) => {
        const due = t.due_date ? new Date(t.due_date) : null;
        const diff = due ? (due - new Date()) / (1000 * 3600 * 24) : 9999;

        const urgent = diff <= 3;
        const important = t.importance >= 7;

        const el = document.createElement("div");
        el.className = "matrix-item";
        el.innerHTML = `
            <strong>${escape(t.title)}</strong><br>
            <small>ID:${t.id} · Due:${t.due_date || "—"} · Eff:${t.estimated_hours}h</small>
        `;

        if (urgent && important)
            document.querySelector("#doFirst .matrix-content").appendChild(el);
        else if (!urgent && important)
            document.querySelector("#schedule .matrix-content").appendChild(el);
        else if (urgent && !important)
            document.querySelector("#delegate .matrix-content").appendChild(el);
        else
            document.querySelector("#eliminate .matrix-content").appendChild(el);
    });
}


// -----------------------------------------------------
// DRAG & DROP
// -----------------------------------------------------
taskTemplate.addEventListener("dragstart", () => taskTemplate.classList.add("dragging"));
taskTemplate.addEventListener("dragend", () => taskTemplate.classList.remove("dragging"));

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));

dropZone.addEventListener("drop", () => {
    dropZone.classList.remove("drag-over");
    openCreateModal();
});


// -----------------------------------------------------
// MODAL
// -----------------------------------------------------
function openCreateModal() {
    modalMode = "create";
    editTaskId = null;

    document.getElementById("modal_title").value = "";
    document.getElementById("modal_due").value = "";
    document.getElementById("modal_hours").value = 1;
    document.getElementById("modal_importance").value = 5;
    document.getElementById("modal_deps").value = "";

    showModal();
}

function openEditModal(id) {
    modalMode = "edit";
    editTaskId = id;

    const t = tasks.find((x) => x.id === id);
    if (!t) return;

    document.getElementById("modal_title").value = t.title;
    document.getElementById("modal_due").value = t.due_date || "";
    document.getElementById("modal_hours").value = t.estimated_hours;
    document.getElementById("modal_importance").value = t.importance;
    document.getElementById("modal_deps").value = t.dependencies.join(",");

    showModal();
}

function showModal() {
    modal.classList.add("show");
    modal.style.display = "flex";
}

function closeModal() {
    modal.classList.remove("show");
    setTimeout(() => (modal.style.display = "none"), 250);
}

modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
});

closeModalBtn.addEventListener("click", closeModal);

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
});


// ★ Unified save handler
saveTaskBtn.addEventListener("click", () => {
    const title = document.getElementById("modal_title").value.trim();
    const due = document.getElementById("modal_due").value || null;
    const hours = Number(document.getElementById("modal_hours").value);
    const imp = Number(document.getElementById("modal_importance").value);
    const d = deps(document.getElementById("modal_deps").value);

    if (!title) return alert("Enter title.");
    if (!hours || hours <= 0) return alert("Invalid estimated hours.");
    if (imp < 1 || imp > 10) return alert("Importance must be 1–10.");

    if (modalMode === "create") {
        tasks.push(
            normalizeTask(
                { title, due_date: due, estimated_hours: hours, importance: imp, dependencies: d },
                nextId()
            )
        );
    } else {
        const t = tasks.find((x) => x.id === editTaskId);
        if (t) {
            t.title = title;
            t.due_date = due;
            t.estimated_hours = hours;
            t.importance = imp;
            t.dependencies = d;
        }
    }

    renderList();
    closeModal();
});


// -----------------------------------------------------
// DELETE TASK
// -----------------------------------------------------
function deleteTask(id) {
    if (!confirm("Delete task?")) return;
    tasks = tasks.filter((t) => t.id !== id);
    renderList();
}


// -----------------------------------------------------
// AUTO-SELECT NUMBER INPUTS
// -----------------------------------------------------
document.querySelectorAll("input[type='number']").forEach((el) =>
    el.addEventListener("focus", () => el.select())
);


// -----------------------------------------------------
// INITIAL RENDER
// -----------------------------------------------------
renderList();
