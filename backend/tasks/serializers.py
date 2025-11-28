from rest_framework import serializers
from datetime import datetime, date


class TaskInputSerializer(serializers.Serializer):
    """
    Represents a single task.
    All fields have safe defaults and validation.
    """
    id = serializers.IntegerField(required=True)
    title = serializers.CharField(required=True, max_length=255)
    due_date = serializers.DateField(required=False, allow_null=True)

    estimated_hours = serializers.FloatField(
        required=False,
        default=1.0,
        min_value=0
    )

    importance = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10
    )

    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )


class HolidayField(serializers.ListField):
    """
    Custom list field to validate holiday strings such as:
      ["2025-01-14", "2025-12-25"]

    Converts them into Python datetime.date objects.
    Ensures strict date validation.
    """
    child = serializers.DateField()

    def to_internal_value(self, data):
        # Handle empty value
        if not data:
            return []

        parsed_list = []

        for item in data:
            if isinstance(item, date):
                parsed_list.append(item)
                continue

            if isinstance(item, str):
                # Strict ISO format YYYY-MM-DD
                try:
                    parsed_list.append(
                        datetime.strptime(item, "%Y-%m-%d").date()
                    )
                except ValueError:
                    raise serializers.ValidationError(
                        f"Invalid holiday format: '{item}'. Expected YYYY-MM-DD."
                    )
                continue

            raise serializers.ValidationError(
                f"Invalid holiday value: {item}. Must be string or date."
            )

        return parsed_list


class AnalyzeRequestSerializer(serializers.Serializer):
    """
    Input schema for:
        POST /api/tasks/analyze/
        POST /api/tasks/suggest/
    """

    # REQUIRED
    tasks = TaskInputSerializer(many=True)

    # OPTIONAL — user-defined weights
    weights = serializers.DictField(
        child=serializers.FloatField(),
        required=False
    )

    # OPTIONAL — one of:
    # "smart", "fastest", "impact", "deadline"
    strategy = serializers.CharField(
        required=False,
        allow_blank=True
    )

    # OPTIONAL — list of custom holiday dates
    # Script.js sends:
    #    holidays: []  OR  ["2025-01-15", "2025-10-26"]
    holidays = HolidayField(required=False, default=list)
