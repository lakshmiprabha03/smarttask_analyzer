# scoring.py
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Any, Set, Iterable

DEFAULT_WEIGHTS = {"urgency": 0.4, "importance": 0.3, "effort": 0.2, "dependency": 0.1}

STRATEGY_PRESETS = {
    "smart": DEFAULT_WEIGHTS,
    "fastest": {"urgency": 0.2, "importance": 0.2, "effort": 0.5, "dependency": 0.1},
    "impact": {"urgency": 0.2, "importance": 0.6, "effort": 0.1, "dependency": 0.1},
    "deadline": {"urgency": 0.7, "importance": 0.15, "effort": 0.1, "dependency": 0.05},
}

# --------- INDIAN HOLIDAYS (examples for 2025; keep this list updated) ----------
INDIAN_HOLIDAYS = [
    date(2025, 1, 14),   # Pongal
    date(2025, 1, 26),   # Republic Day
    date(2025, 8, 15),   # Independence Day
    date(2025, 10, 20),  # Diwali (approx)
    date(2025, 10, 2),   # Gandhi Jayanthi
    date(2025, 12, 25),  # Christmas
]


# -------------------- Utilities --------------------
def _parse_date(d) -> date | None:
    """Accept date, or ISO string 'YYYY-MM-DD', return date or None."""
    if d is None:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # Accept strict ISO format
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            # try loose fallback (day-first common cases)
            try:
                return datetime.strptime(d, "%d-%m-%Y").date()
            except Exception:
                return None
    return None


def _parse_holidays(raw: Iterable[Any]) -> Set[date]:
    """Accept iterable of str/date and return set of date objects."""
    out = set()
    if not raw:
        return out
    for item in raw:
        d = _parse_date(item)
        if d:
            out.add(d)
    return out


def _is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5=Saturday,6=Sunday


def business_days_between(start: date, end: date, holidays: Set[date]) -> int:
    """
    Count business days from start (exclusive) to end (inclusive).
    - If end >= start: returns positive number of business days until end.
    - If end < start: returns negative number of business days overdue (i.e. how many business days passed since end).
    Excludes weekends and holiday dates in `holidays`.
    """
    if start == end:
        return 0 if (_is_weekend(end) or end in holidays) else 0

    step = 1 if end > start else -1
    count = 0
    cur = start + timedelta(days=step)
    while (cur <= end and step > 0) or (cur >= end and step < 0):
        if not _is_weekend(cur) and cur not in holidays:
            count += step
        cur = cur + timedelta(days=step)
    return count


def detect_cycles(tasks: List[Dict[str, Any]]) -> Tuple[bool, List[List[int]]]:
    """
    Detect cycles in dependency graph; return (has_cycle, list_of_cycles)
    Each cycle is a list of task ids (ordered as discovered).
    """
    graph = {t["id"]: list(t.get("dependencies") or []) for t in tasks}
    visited = {}
    cycles: List[List[int]] = []

    def dfs(node: int, stack: List[int]):
        if visited.get(node) == 1:
            # found a back edge
            if node in stack:
                idx = stack.index(node)
                cycles.append(stack[idx:] + [node])
            return
        if visited.get(node) == 2:
            return

        visited[node] = 1
        stack.append(node)
        for nei in graph.get(node, []):
            if nei in graph:  # ignore unknown deps
                dfs(nei, stack)
        stack.pop()
        visited[node] = 2

    for n in graph:
        if visited.get(n) is None:
            dfs(n, [])
    return (len(cycles) > 0, cycles)


def _count_dependents(tasks_map: Dict[int, Dict]) -> Dict[int, int]:
    dependents = {tid: 0 for tid in tasks_map.keys()}
    for t in tasks_map.values():
        for dep in t.get("dependencies") or []:
            if dep in dependents:
                dependents[dep] += 1
    return dependents


# -------------------- Main scoring --------------------
def compute_scores(
    tasks: List[Dict[str, Any]],
    weights: Dict[str, float] | None = None,
    today: date | None = None,
    holidays: Iterable[Any] | None = None
) -> List[Dict[str, Any]]:
    """
    Compute task priority scores (0-100) with date intelligence.

    Parameters:
      - tasks: list of dicts with keys id, title, due_date (YYYY-MM-DD | date | None),
               estimated_hours, importance, dependencies
      - weights: optional dict overriding DEFAULT_WEIGHTS
      - today: optional reference date (useful for tests)
      - holidays: optional iterable of date or 'YYYY-MM-DD' strings (custom holidays)

    Behavior:
      - Uses business days until due (excludes weekends and holidays) as urgency signal.
      - Overdue is computed in business days; larger overdue => higher urgency.
      - Tasks without a due_date get a low/neutral urgency.
      - Effort favors quick wins: 10 / (1 + hours)
      - Dependency score = number of tasks that depend on this task (incoming edges)
      - Circular dependencies are flagged (do not fail scoring)
    """

    today = today or date.today()
    weights = weights or DEFAULT_WEIGHTS

    # Defensive normalization of weights
    total = sum(weights.values()) if weights else 0
    if not total or total <= 0:
        weights = DEFAULT_WEIGHTS.copy()
        total = sum(weights.values())
    weights = {k: float(v) / total for k, v in weights.items()}

    # build holiday set (merge built-in Indian holidays + user)
    final_holidays: Set[date] = set(INDIAN_HOLIDAYS)
    if holidays:
        final_holidays |= _parse_holidays(holidays)

    # Build tasks map and normalize fields
    tasks_map: Dict[int, Dict[str, Any]] = {t["id"]: t.copy() for t in tasks}
    for t in tasks_map.values():
        t.setdefault("importance", 5)
        t.setdefault("estimated_hours", 1.0)
        t.setdefault("dependencies", [])
        t["_due_date_obj"] = _parse_date(t.get("due_date"))

    dependents_count = _count_dependents(tasks_map)
    has_cycle, cycles = detect_cycles(tasks)
    cycle_nodes: Set[int] = {n for c in cycles for n in c}

    results: List[Dict[str, Any]] = []

    for tid, t in tasks_map.items():
        explanation_parts: List[str] = []

        due_obj = t.get("_due_date_obj")
        # default urgency (no due date)
        if due_obj is None:
            urgency = 2.5  # neutral-low urgency if no due date
            explanation_parts.append("no due date (low urgency)")
            # still add flags if needed (none in this case)
        else:
            # compute business days until due (positive means due in future, 0 means today if business day)
            bdays = business_days_between(today, due_obj, final_holidays)

            # Flag if due falls on weekend or holiday (calendar day)
            if _is_weekend(due_obj):
                explanation_parts.append("due on weekend")
            if due_obj in final_holidays:
                explanation_parts.append("due on holiday")

            if bdays < 0:
                # Overdue in business days
                overdue_days = abs(bdays)
                # larger overdue => larger urgency. capped to avoid runaway
                urgency = min(15.0, 10.0 + overdue_days * 0.9)
                explanation_parts.append(f"overdue by {overdue_days} business days")
            else:
                # Map business days to 0-10 urgency: nearer => higher
                # smoother decay than linear: urgency = max(0, 10 - (bdays / 2))
                urgency = max(0.0, 10.0 - (bdays / 2.0))
                explanation_parts.append(f"{bdays} business days until due")

                # If the due falls on a weekend we slightly reduce urgency because actual working day is later
                if _is_weekend(due_obj):
                    urgency *= 0.75
                    explanation_parts.append("weekend adjustment applied")

                # If the due is holiday, slightly increase urgency (deadline tied to a holiday often means prep earlier)
                if due_obj in final_holidays:
                    urgency *= 1.15
                    explanation_parts.append("holiday adjustment applied")

        # IMPORTANCE (1-10)
        importance = int(max(1, min(10, int(t.get("importance") or 5))))
        explanation_parts.append(f"importance {importance}/10")

        # EFFORT: convert estimated_hours to 0-10 (lower hours -> higher quick win)
        hours = float(t.get("estimated_hours") or 1.0)
        effort = 10.0 / (1.0 + max(0.0, hours))
        explanation_parts.append(f"estimated_hours {hours}")

        # DEPENDENCY: number of tasks that depend on this
        dep_score = int(dependents_count.get(tid, 0))
        if dep_score:
            explanation_parts.append(f"blocks {dep_score} task(s)")

        # CIRCULAR DEPENDENCY
        circular = tid in cycle_nodes
        if circular:
            explanation_parts.append("circular dependency detected")

        # Weighted raw score
        raw_score = (
            weights.get("urgency", 0.0) * float(urgency)
            + weights.get("importance", 0.0) * float(importance)
            + weights.get("effort", 0.0) * float(effort)
            + weights.get("dependency", 0.0) * float(dep_score)
        )

        # Soft normalization divisor: estimate max for each component
        max_dependents = max(1, max(dependents_count.values() or [1]))
        normalization_divisor = (
            weights.get("urgency", 0.0) * 15.0
            + weights.get("importance", 0.0) * 10.0
            + weights.get("effort", 0.0) * 10.0
            + weights.get("dependency", 0.0) * float(max_dependents)
        )
        if normalization_divisor <= 0:
            score = round(raw_score * 10.0, 2)
        else:
            score = round((raw_score / normalization_divisor) * 100.0, 2)

        results.append({
            "id": tid,
            "title": t.get("title"),
            "due_date": t.get("due_date"),
            "estimated_hours": hours,
            "importance": importance,
            "dependencies": t.get("dependencies") or [],
            "score": score,
            "explanation": "; ".join(explanation_parts),
            "circular_dependency": circular
        })

    # Sort: circular_dependency flagged first for reviewer visibility, then by score desc
    results.sort(key=lambda x: (x["circular_dependency"], x["score"]), reverse=True)
    return results
