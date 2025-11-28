from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AnalyzeRequestSerializer
from .scoring import (
    compute_scores,
    STRATEGY_PRESETS,
    detect_cycles,
    DEFAULT_WEIGHTS,
)

from datetime import date


# -----------------------------------------
# INDIAN HOLIDAY LIST (Fixed Known Dates)
# -----------------------------------------
INDIAN_HOLIDAYS = {
    "2025-01-14",  # Pongal
    "2025-01-26",  # Republic Day
    "2025-10-02",  # Gandhi Jayanthi
    "2025-08-15",  # Independence Day
    "2025-10-20",  # Diwali
    "2025-12-25",  # Christmas
}
INDIAN_HOLIDAYS = {date.fromisoformat(d) for d in INDIAN_HOLIDAYS}


# -----------------------------------------
# GLOBAL LEARNING WEIGHTS
# -----------------------------------------
LEARNING_WEIGHTS = DEFAULT_WEIGHTS.copy()


# -----------------------------------------
# UTILITY: Resolve final holiday list
# -----------------------------------------
def resolve_holidays(mode: str, custom_list):
    """
    Convert holiday mode + custom list into the final holiday list.

    Modes supported:
        none     → []
        indian   → fixed Indian list
        custom   → user list
        both     → user list + Indian
    """

    if mode == "none":
        return []

    if mode == "indian":
        return list(INDIAN_HOLIDAYS)

    if mode == "custom":
        return custom_list

    if mode == "both":
        return list(INDIAN_HOLIDAYS.union(set(custom_list)))

    # default safe fallback
    return custom_list


# ======================================================================
#                           ANALYZE VIEW
# ======================================================================
class AnalyzeView(APIView):

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        tasks = payload["tasks"]

        # ---------- Weight Selection ----------
        strategy = (payload.get("strategy") or "").lower()

        # Base weights = learned weights (AI learning)
        weights = payload.get("weights") or LEARNING_WEIGHTS

        # If strategy override selected
        if strategy in STRATEGY_PRESETS:
            weights = STRATEGY_PRESETS[strategy]

        # ---------- Resolve Holidays ----------
        custom_holidays = payload.get("holidays", [])
        holiday_mode = request.data.get("holiday_mode", "none")  # string from frontend

        holidays_final = resolve_holidays(holiday_mode, custom_holidays)

        # ---------- Cycle Detection ----------
        has_cycle, cycles = detect_cycles(tasks)

        # ---------- Score Computation ----------
        results = compute_scores(
            tasks,
            weights=weights,
            holidays=holidays_final
        )

        return Response({
            "meta": {
                "strategy": strategy or "smart",
                "has_cycle": has_cycle,
                "cycles": cycles,
                "final_weights": weights,
                "holiday_mode": holiday_mode,
                "holidays_used": [str(d) for d in holidays_final]
            },
            "tasks": results
        }, status=status.HTTP_200_OK)


# ======================================================================
#                           SUGGEST VIEW
# ======================================================================
class SuggestView(APIView):

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        tasks = payload["tasks"]

        # ---------- Weight Selection ----------
        strategy = (payload.get("strategy") or "").lower()
        weights = payload.get("weights") or LEARNING_WEIGHTS

        if strategy in STRATEGY_PRESETS:
            weights = STRATEGY_PRESETS[strategy]

        # ---------- Resolve Holidays ----------
        custom_holidays = payload.get("holidays", [])
        holiday_mode = request.data.get("holiday_mode", "none")

        holidays_final = resolve_holidays(holiday_mode, custom_holidays)

        # ---------- Compute Scores ----------
        results = compute_scores(
            tasks,
            weights=weights,
            holidays=holidays_final
        )

        # Top 3 suggestions
        top3 = results[:3]
        suggested = []

        for t in top3:
            why = []

            if t["circular_dependency"]:
                why.append("Circular dependency — resolves blockers")

            if "overdue" in t["explanation"]:
                why.append("Overdue — needs immediate action")

            if t["estimated_hours"] <= 1.5:
                why.append("Quick win — low effort")

            if t["importance"] >= 8:
                why.append("High impact task")

            if not why:
                why.append("Balanced priority task")

            suggested.append({**t, "why": "; ".join(why)})

        return Response({"suggestions": suggested}, status=status.HTTP_200_OK)


# ======================================================================
#                           FEEDBACK VIEW
# ======================================================================
class FeedbackView(APIView):
    """
    POST /api/tasks/feedback/
    Body:
        {
            "helpful": true/false,
            "score": 70.2
        }
    """

    def post(self, request):
        global LEARNING_WEIGHTS

        helpful = request.data.get("helpful")
        score = float(request.data.get("score", 0))

        if helpful is None:
            return Response({"error": "helpful (boolean) required"}, status=400)

        # ---------- Learning Logic ----------
        if helpful:
            LEARNING_WEIGHTS["importance"] += 0.03
            LEARNING_WEIGHTS["urgency"] += 0.02
        else:
            LEARNING_WEIGHTS["effort"] += 0.03

        # ---------- Normalize Weights ----------
        total = sum(LEARNING_WEIGHTS.values())
        LEARNING_WEIGHTS = {k: v / total for k, v in LEARNING_WEIGHTS.items()}

        return Response({
            "message": "Feedback recorded — model improved",
            "new_weights": LEARNING_WEIGHTS
        }, status=200)
