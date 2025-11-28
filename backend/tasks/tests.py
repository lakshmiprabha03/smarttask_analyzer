from django.test import TestCase
from datetime import date, timedelta
from .scoring import compute_scores, detect_cycles


class ScoringTests(TestCase):

    def setUp(self):
        # Fixed reference date for deterministic tests
        self.today = date(2025, 1, 10)

    # ---------------------------------------------------
    # Test 1 — Overdue tasks get higher score (business days)
    # ---------------------------------------------------
    def test_business_day_overdue(self):
        tasks = [
            {
                "id": 1, "title": "future",
                "due_date": "2025-01-20",  # future
                "estimated_hours": 3, "importance": 5, "dependencies": []
            },
            {
                "id": 2, "title": "overdue",
                "due_date": "2025-01-05",  # past date
                "estimated_hours": 3, "importance": 5, "dependencies": []
            },
        ]

        results = compute_scores(tasks, today=self.today)
        scores = {r["id"]: r["score"] for r in results}

        self.assertTrue(scores[2] > scores[1], "Overdue task must score higher than future task")

    # ---------------------------------------------------
    # Test 2 — Quick win tasks score higher
    # ---------------------------------------------------
    def test_quick_win_boost(self):
        tasks = [
            {
                "id": 1, "title": "long",
                "due_date": "2025-01-20",
                "estimated_hours": 10, "importance": 5, "dependencies": []
            },
            {
                "id": 2, "title": "quick",
                "due_date": "2025-01-20",
                "estimated_hours": 0.5, "importance": 5, "dependencies": []
            },
        ]

        results = compute_scores(tasks, today=self.today)
        scores = {r["id"]: r["score"] for r in results}

        self.assertTrue(scores[2] > scores[1], "Quick tasks must score higher than long tasks")

    # ---------------------------------------------------
    # Test 3 — Weekend due date reduces urgency
    # ---------------------------------------------------
    def test_weekend_reduction(self):
        tasks = [
            {
                "id": 1, "title": "weekday",
                "due_date": "2025-01-13",  # Monday
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
            {
                "id": 2, "title": "weekend",
                "due_date": "2025-01-12",  # Sunday
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
        ]

        results = compute_scores(tasks, today=self.today)
        weekday = [r for r in results if r["id"] == 1][0]
        weekend = [r for r in results if r["id"] == 2][0]

        self.assertTrue(
            weekday["score"] > weekend["score"],
            "Weekend due date should reduce urgency"
        )

    # ---------------------------------------------------
    # Test 4 — Holiday increases urgency
    # ---------------------------------------------------
    def test_holiday_increases_urgency(self):
        # Jan 14 = Pongal (in Indian list)
        tasks = [
            {
                "id": 1, "title": "normal",
                "due_date": "2025-01-13",
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
            {
                "id": 2, "title": "holiday",
                "due_date": "2025-01-14",  # Pongal
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
        ]

        results = compute_scores(tasks, today=self.today)
        normal = [r for r in results if r["id"] == 1][0]
        holiday = [r for r in results if r["id"] == 2][0]

        self.assertTrue(
            holiday["score"] > normal["score"],
            "Holiday due date should increase urgency"
        )

    # ---------------------------------------------------
    # Test 5 — Custom holiday increases urgency
    # ---------------------------------------------------
    def test_custom_holiday(self):
        tasks = [
            {
                "id": 1, "title": "normal",
                "due_date": "2025-01-18",
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
            {
                "id": 2, "title": "custom_holiday",
                "due_date": "2025-01-17",
                "estimated_hours": 2, "importance": 5, "dependencies": []
            },
        ]

        results = compute_scores(
            tasks,
            today=self.today,
            holidays=["2025-01-17"]   # custom holiday
        )

        normal = [r for r in results if r["id"] == 1][0]
        special = [r for r in results if r["id"] == 2][0]

        self.assertTrue(
            special["score"] > normal["score"],
            "Custom holiday must increase urgency"
        )

    # ---------------------------------------------------
    # Test 6 — Circular dependencies detected
    # ---------------------------------------------------
    def test_detect_cycle(self):
        tasks = [
            {"id": 1, "title": "A", "dependencies": [2]},
            {"id": 2, "title": "B", "dependencies": [3]},
            {"id": 3, "title": "C", "dependencies": [1]},
        ]

        has_cycle, cycles = detect_cycles(tasks)

        self.assertTrue(has_cycle, "Cycle must be detected")
        self.assertTrue(len(cycles) > 0, "Cycle list should not be empty")
        self.assertTrue({1, 2, 3}.issubset(set(cycles[0])), "Cycle must contain IDs 1,2,3")

    # ---------------------------------------------------
    # Test 7 — Sorting places circular deps on top
    # ---------------------------------------------------
    def test_circular_sort_priority(self):
        tasks = [
            {"id": 1, "title": "A", "dependencies": [2], "due_date": "2025-01-20"},
            {"id": 2, "title": "B", "dependencies": [1], "due_date": "2025-01-20"},
            {"id": 3, "title": "C", "dependencies": [], "due_date": "2025-01-20"},
        ]

        results = compute_scores(tasks, today=self.today)

        # circular tasks must come before non-circular in sorted order
        circular_ids = [t["id"] for t in results[:2]]
        self.assertIn(1, circular_ids)
        self.assertIn(2, circular_ids)
        self.assertEqual(results[-1]["id"], 3)
