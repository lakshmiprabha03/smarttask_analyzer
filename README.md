# 🧠 Smart Task Analyzer  
A full-stack intelligent task prioritization system built.  
This system uses a scoring algorithm to prioritize tasks, supports multiple strategies, handles dependencies, visualizes graphs, highlights cycles, and generates an Eisenhower Matrix — all wrapped in a modern, responsive, glass-themed UI.

---

# 📌 Overview

Smart Task Analyzer helps users:

✔ Prioritize tasks based on urgency, importance, effort, and dependencies  
✔ Choose different prioritization *strategies*  
✔ Add tasks manually, via bulk JSON, or by drag-and-drop  
✔ Visualize task dependencies as a graph  
✔ Detect circular dependencies  
✔ View tasks inside an Eisenhower Decision Matrix  
✔ Use Indian/custom holidays in scheduling  
✔ Get top 3 suggestions + submit feedback (AI-like feature)

This project demonstrates:

- Backend engineering & API design  
- Scoring algorithms  
- Frontend engineering (layout, UX, modular JS)  
- Data visualization  
- State management  
- Clean code practices  

---

# 🧩 Architecture Overview

```

Frontend (HTML + CSS + JS)
↳ Sends tasks + strategy + holidays
↳ Renders suggestions, graphs, matrix, UI

Backend (Django + DRF)
↳ Scoring Algorithm
↳ Suggestion Engine
↳ Holiday-aware urgency
↳ Cycle detection
↳ Feedback endpoint

````

---

# 🛠 Tech Stack

### **Backend**
- Python  
- Django  
- Django REST Framework  
- SQLite  

### **Frontend**
- HTML5  
- CSS3 (Glassmorphism, responsive grid)  
- Vanilla JavaScript  
- vis-network.js (dependency graph)  

---

# ⚙️ How to Run (Backend)

```sh
cd smarttask_analyzer/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
````

API Base URL:

```
http://127.0.0.1:8000/api/tasks/
```

---

# 🌐 Frontend Setup

Simply open:

```
smarttask_analyzer/frontend/index.html
```

Or run a local server:

```sh
python -m http.server 5500
```

Visit:

```
http://localhost:5500/index.html
```

---

# 🧮 Algorithm Breakdown 

The scoring engine evaluates four factors:

---

## 1️⃣ Urgency (Due Date Based)

* Tasks due soon → higher urgency
* Overdue tasks → maximum urgency
* Due-date-missing tasks → neutral
* Holidays are excluded before calculating effective days

---

## 2️⃣ Importance (User Rated)

* Scale: 1 to 10
* Clamped for safety
* Weighted more heavily in *High Impact* strategy

---

## 3️⃣ Effort (Quick Wins)

Formula:

```
quick_win_score = 10 / (1 + estimated_hours)
```

Low-effort tasks get a reward.

---

## 4️⃣ Dependency Influence

Tasks that unblock other tasks earn extra points.

---

# 🔢 Final Weighted Score (Normalized 0–100)

Default:

```
urgency:    0.4
importance: 0.3
effort:     0.2
dependency: 0.1
```

---

# 🎛 Task Prioritization Strategies 

| Strategy        | Meaning                          |
| --------------- | -------------------------------- |
| Smart Balance   | Balanced across all four factors |
| Fastest Wins    | Quick tasks get boosted          |
| High Impact     | Importance dominates             |
| Deadline Driven | Urgency dominates                |

---

# 🧩 Key Design Decisions

### ✔ `scoring.py` for algorithm

Keeps business logic separate and testable.

### ✔ Stateless API

Tasks are not saved permanently — matches assignment requirement.

### ✔ Cycle Detection

DFS-based detection highlights cyclic task nodes in red.

### ✔ Holiday-Aware Urgency

Indian holidays + custom user-defined holidays supported.

### ✔ Minimal Frontend Dependencies

Everything is implemented in pure JS except Vis.js.

---

# ⭐ Final Bonus Features 

### ⭐ 1. Dependency Graph Visualization

* Hierarchical layout
* Vis-network rendering
* Cycles highlighted in **red**
* Nodes show title + ID

### ⭐ 2. Eisenhower Matrix

Based on:

* Urgent = due in ≤ 3 days
* Important = importance ≥ 7

Quadrants:

* **Do First**
* **Schedule**
* **Delegate**
* **Eliminate**

### ⭐ 3. Top 3 Suggestions 

Includes:

* Score
* Explanation
* “Why this matters?”
* Feedback buttons

### ⭐ 4. Feedback Learning API

```
POST /api/tasks/feedback/
```

Saves:

* helpful / not helpful
* task_id
* score

---

# 🎨 Frontend UI / UX 

This version includes:

✔ hybrid dashboard
✔ Left sidebar (strategy + holiday + drag-drop)
✔ Right panel (manual tasks + analysis + results)
✔ Fully centered blur-background **modal**
✔ Floating labels
✔ Responsive grid
✔ Clean spacing & alignment

---

# 🧪 Unit Tests (Backend)

Located in:

```
backend/tasks/tests.py
```

Covers:

* Urgency math
* Effort scoring
* Missing due dates
* Cycle detection
* Strategies
* API response format

---

# 🧠 Edge Cases Handled

✔ Missing due dates
✔ Estimated hours = 0 or negative
✔ Invalid importance (clamped)
✔ Duplicate task IDs
✔ Invalid JSON
✔ Circular dependencies
✔ Strategy mismatch
✔ Holiday JSON errors
✔ No tasks → user notified

---

# 📂 Project Structure

```
/frontend
    index.html
    styles.css
    script.js

/backend
    manage.py
    tasks/
        scoring.py
        serializers.py
        views.py
        urls.py
        tests.py
        ...

README.md
```

---

# 🕒 Time Breakdown

| Task                      | Time     |
| ------------------------- |----------|
| Backend design            | ~1 hr    |
| Scoring + cycle detection | ~1 hr    |
| Frontend UI               | ~1.5 hrs |
| Visualization + Matrix    | ~1.5 hr  |
| Drag & Drop + Modal       | ~40 mins |
| Testing + debugging       | ~40 mins |
| README + cleanup          | ~1 hr    |

Total: **~7 hours** (with bonus features)

---

# 🚀 Future Improvements

* User accounts + persistent task storage
* Custom weight configuration
* Export PDF / CSV
* Live drag arrangement
* ML-based adaptive prioritization

---

# 📸 Screenshots 
